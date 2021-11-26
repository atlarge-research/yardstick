package main

import (
	"archive/zip"
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"mime/multipart"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path"
	"path/filepath"
	"strconv"
	"strings"
	"sync/atomic"
	"time"
)

type Node struct {
	// User used to log in to the remote node
	user string
	// Host or IP of the remote node, reachable from the sshClient.
	host string
	// A jump host proxy used to reach the node
	jumpHost string
	// The remote port on which YS is running.
	remotePort uint64
	// The command that keeps open a local tunnel to the remote HTTP server
	tunnel *exec.Cmd
	// The local address tunneled to the remote node via SSH.
	localAddress *url.URL
	// The client used to make HTTP call on the localAddress.
	client *http.Client
	// Remote location of YS
	tmpDirPath string
	// Remote location of the YS executable
	tmpFilePath string
	// Remote location of the YS log file
	tmpLogFilePath string
}

var portCounter uint64 = 9000

func nextPort() uint64 {
	return atomic.AddUint64(&portCounter, 1)
}

func ResetPort() {
	portCounter = 9000
}

func (node *Node) scpCommand(local, remote string) *exec.Cmd {
	args := make([]string, 0)
	if node.jumpHost != "" {
		args = append(args, "-J", node.jumpHost)
	}
	args = append(args, local, remote)
	return exec.Command("scp", args...)
}

func (node *Node) sshCommand(command string, args ...string) *exec.Cmd {
	commandArgs := make([]string, 0)
	commandArgs = append(commandArgs, "-o", "StrictHostKeyChecking=accept-new")
	if node.jumpHost != "" {
		commandArgs = append(commandArgs, fmt.Sprintf("-J %v", node.jumpHost))
	}
	commandArgs = append(commandArgs, fmt.Sprintf("%v@%v", node.user, node.host))
	commandArgs = append(commandArgs, command)
	commandArgs = append(commandArgs, args...)
	return exec.Command("ssh", commandArgs...)
}

func NewNode(user, host, proxy, binary string) *Node {
	node := &Node{
		user:     user,
		host:     host,
		jumpHost: proxy,
		client:   &http.Client{Timeout: 10 * time.Second},
	}
	// Create remote file using SSH client
	mktempCmd := node.sshCommand("mktemp", "-d")
	tmpDirBytes, err := mktempCmd.Output()
	if err != nil {
		panic(err)
	}
	node.tmpDirPath = strings.TrimSpace(string(tmpDirBytes))
	log.Printf("remote deployment at %v", node.tmpDirPath)
	node.tmpFilePath = path.Join(node.tmpDirPath, "ys")
	node.tmpLogFilePath = path.Join(node.tmpDirPath, "ys.log")

	// Use SSH client to create SFTP client
	scpCmd := node.scpCommand(binary, fmt.Sprintf("%v@%v:%v", user, host, node.tmpFilePath))
	if err := scpCmd.Run(); err != nil {
		panic(err)
	}

	node.remotePort = nextPort()
	// Make remote tmp file executable and run it
	startCmd := node.sshCommand("cd", node.tmpDirPath, ";",
		"chmod", "+x", node.tmpFilePath, ";",
		"nohup", node.tmpFilePath, "--worker", "--port", strconv.Itoa(int(node.remotePort)),
		"<", "/dev/null", ">", node.tmpLogFilePath, "2>&1", "&")
	if err := startCmd.Run(); err != nil {
		panic(err)
	}

	var jump string
	if proxy == "" {
		jump = "localhost"
	} else {
		jump = proxy
	}
	nodeLocalPort := nextPort()
	tunnelCmd := exec.Command("ssh", "-o", "StrictHostKeyChecking=accept-new", "-N", "-L",
		fmt.Sprintf("%v:%v:%v", nodeLocalPort, host, node.remotePort), jump)
	if err := tunnelCmd.Start(); err != nil {
		panic(err)
	}
	node.tunnel = tunnelCmd

	laddr, err := url.Parse(fmt.Sprintf("http://localhost:%v", nodeLocalPort))
	if err != nil {
		panic(err)
	}
	node.localAddress = laddr
	return node
}

func (node *Node) Close() error {
	defer func() {
		node.tunnel.Process.Signal(os.Interrupt)
		qChan := make(chan error)
		go func() {
			_, err := node.tunnel.Process.Wait()
			qChan <- err
		}()
		select {
		case <-qChan:
		case <-time.After(3 * time.Second):
			node.tunnel.Process.Kill()
		}
	}()
	resp, err := node.client.Get(fmt.Sprintf("%v/close", node.localAddress))
	if err != nil {
		return fmt.Errorf("could not GET from node: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		bodyString, err := io.ReadAll(resp.Body)
		if err != nil {
			return fmt.Errorf("could not read response from node: %w", err)
		}
		return fmt.Errorf("node returned non-200: %v", string(bodyString))
	}
	time.Sleep(2 * time.Second)
	if err := node.sshCommand("rm", "-rf", node.tmpDirPath).Run(); err != nil {
		return fmt.Errorf("could not remote tmp dir on node: %w", err)
	}
	return nil
}

func (node *Node) Create(name string) (string, error) {
	response, err := node.client.Get(fmt.Sprintf("%v/program/create/%v", node.localAddress, name))
	if err != nil {
		return "", fmt.Errorf("could not GET from node: %w", err)
	}
	defer response.Body.Close()
	responseBytes, err := io.ReadAll(response.Body)
	if err != nil {
		return "", fmt.Errorf("could not read response from node: %w", err)
	}
	return string(responseBytes), nil
}

func (node *Node) UploadToPath(uuid, filePath, remotePath string) error {
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("could not open file: %w", err)
	}
	defer file.Close()
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)
	pathPart, err := writer.CreateFormField("path")
	if err != nil {
		return fmt.Errorf("could not create form field: %w", err)
	}
	if _, err := pathPart.Write([]byte(filepath.Dir(remotePath))); err != nil {
		return fmt.Errorf("could not write remote dir: %w", err)
	}
	filePart, err := writer.CreateFormFile("file", filepath.Base(remotePath))
	if err != nil {
		return fmt.Errorf("could not create file form field: %w", err)
	}
	if _, err = io.Copy(filePart, file); err != nil {
		return fmt.Errorf("could not copy file: %w", err)
	}
	if err = writer.Close(); err != nil {
		return fmt.Errorf("could not close writer: %w", err)
	}
	response, err := node.client.Post(fmt.Sprintf("%v/program/upload/%v", node.localAddress, uuid), writer.FormDataContentType(), body)
	if err != nil {
		return fmt.Errorf("could not POST to node: %w", err)
	}
	defer response.Body.Close()
	if response.StatusCode != 200 {
		responseBody, err := io.ReadAll(response.Body)
		if err != nil {
			return fmt.Errorf("could not read node response: %w", err)
		}
		return fmt.Errorf(string(responseBody))
	}
	return nil
}

func (node *Node) Upload(uuid, localPath string) error {
	return node.UploadToPath(uuid, localPath, filepath.Base(localPath))
}

func (node *Node) Start(uuid, path, logFile string, args ...string) error {
	command := []string{path}
	command = append(command, args...)
	request := StartRequest{
		Command: path,
		Args:    args,
		LogFile: logFile,
	}
	body, err := json.Marshal(request)
	if err != nil {
		panic(err)
	}
	response, err := node.client.Post(fmt.Sprintf("%v/program/start/%v", node.localAddress, uuid),
		"application/json", bytes.NewBuffer(body))
	if err != nil {
		panic(err)
	}
	defer response.Body.Close()
	responseBody, err := io.ReadAll(response.Body)
	if err != nil {
		panic(err)
	}
	responseString := strings.TrimSpace(string(responseBody))
	if response.StatusCode != 200 {
		return errors.New(responseString)
	}
	return nil
}

func (node *Node) Status(uuid string) (Status, error) {
	response, err := node.client.Get(fmt.Sprintf("%v/program/status/%v", node.localAddress, uuid))
	if err != nil {
		return 0, err
	}
	defer response.Body.Close()
	responseBody, err := io.ReadAll(response.Body)
	if err != nil {
		return 0, err
	}
	responseString := strings.TrimSpace(string(responseBody))
	if response.StatusCode != 200 {
		return 0, errors.New(responseString)
	}
	status, err := strconv.Atoi(responseString)
	if err != nil {
		return 0, err
	}
	return Status(status), nil
}

func (node *Node) Stop(uuid string) error {
	response, err := node.client.Get(fmt.Sprintf("%v/program/stop/%v", node.localAddress, uuid))
	if err != nil {
		panic(err)
	}
	defer response.Body.Close()
	if response.StatusCode != 200 {
		responseBody, err := io.ReadAll(response.Body)
		if err != nil {
			panic(err)
		}
		responseString := strings.TrimSpace(string(responseBody))
		return errors.New(responseString)
	}
	return nil
}

func (node *Node) Get(uuid, outputDirPath, prefix string) error {
	ip := strings.ReplaceAll(node.host, ".", "_")
	dirPath := filepath.Join(outputDirPath, fmt.Sprintf("%v-%v-node-%v", prefix, uuid, ip))
	if err := os.MkdirAll(dirPath, 0755); err != nil {
		panic(err)
	}
	response, err := node.client.Get(fmt.Sprintf("%v/program/get/%v", node.localAddress, uuid))
	if err != nil {
		panic(err)
	}
	defer response.Body.Close()
	buf := &bytes.Buffer{}
	io.Copy(buf, response.Body)
	zipReader, err := zip.NewReader(bytes.NewReader(buf.Bytes()), int64(buf.Len()))
	if err != nil {
		panic(err)
	}
	for _, f := range zipReader.File {
		if err := unzipToDir(dirPath, f, outputDirPath); err != nil {
			return err
		}
	}
	return nil
}

func unzipToDir(dirPath string, f *zip.File, outputDirPath string) error {
	filePath := filepath.Join(dirPath, f.Name)

	if !strings.HasPrefix(filePath, filepath.Clean(outputDirPath)+string(os.PathSeparator)) {
		panic(fmt.Sprintf("path join failed: %v\n", filePath))
	}
	if f.FileInfo().IsDir() {
		if err := os.MkdirAll(filePath, os.ModePerm); err != nil {
			return err
		}
	} else {
		if err := os.MkdirAll(filepath.Dir(filePath), os.ModePerm); err != nil {
			panic(err)
		}

		dstFile, err := os.OpenFile(filePath, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, f.Mode())
		if err != nil {
			return err
		}
		defer dstFile.Close()

		fileInArchive, err := f.Open()
		if err != nil {
			return err
		}
		defer fileInArchive.Close()

		if _, err := io.Copy(dstFile, fileInArchive); err != nil {
			return err
		}
	}
	return nil
}
