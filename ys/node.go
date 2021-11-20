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
	"path"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/pkg/sftp"
	"golang.org/x/crypto/ssh"
)

type Node struct {
	host            string
	endpoint        *url.URL
	client          *http.Client
	sshClientConfig *ssh.ClientConfig
	tmpDirPath      string
	tmpFilePath     string
	tmpLogFilePath  string
}

func NewNode(user, keyFilePath, ipAddress string, port int, binary string) (node *Node) {
	nodeURL, err := url.Parse(fmt.Sprintf("http://%v:%v", ipAddress, port))
	if err != nil {
		panic(err)
	}
	node = &Node{}
	node.host = ipAddress
	node.endpoint = nodeURL
	node.client = &http.Client{Timeout: 10 * time.Second}

	// Prepare SSH authentication
	key := readPubKey(keyFilePath)
	node.sshClientConfig = &ssh.ClientConfig{
		User: user,
		Auth: []ssh.AuthMethod{
			key,
		},
		HostKeyCallback: ssh.InsecureIgnoreHostKey(), // XXX: Security issue
	}

	// Create SSH client
	sshClient, err := ssh.Dial("tcp", fmt.Sprintf("%v:22", ipAddress), node.sshClientConfig)

	// Create remote file using SSH client
	tmpFileSession, err := sshClient.NewSession()
	if err != nil {
		panic(err)
	}
	defer tmpFileSession.Close()
	tmpDirBytes, err := tmpFileSession.Output("mktemp -d")
	if err != nil {
		panic(err)
	}
	node.tmpDirPath = strings.TrimSpace(string(tmpDirBytes))
	log.Printf("remote deployment at %v", node.tmpDirPath)
	node.tmpFilePath = path.Join(node.tmpDirPath, "ys")
	node.tmpLogFilePath = path.Join(node.tmpDirPath, "ys.log")

	// Use SSH client to create SFTP client
	sftpClient, err := sftp.NewClient(sshClient)
	if err != nil {
		panic(err)
	}

	// Open tmp file on remote
	dstFile, err := sftpClient.Create(node.tmpFilePath)
	if err != nil {
		panic(err)
	}

	srcFile, err := os.Open(binary)
	if err != nil {
		panic(err)
	}

	// Write current binary into remote tmp file
	if _, err := dstFile.ReadFrom(srcFile); err != nil {
		panic(err)
	}

	srcFile.Close()
	dstFile.Close()
	sftpClient.Close()

	// Make remote tmp file executable and run it
	session, err := sshClient.NewSession()
	defer session.Close()
	if err := session.Start(
		fmt.Sprintf("cd %v &&", node.tmpDirPath) +
			fmt.Sprintf(" chmod +x %v &&", node.tmpFilePath) +
			fmt.Sprintf(" nohup %v --worker --port %v", node.tmpFilePath, node.endpoint.Port()) +
			fmt.Sprintf(" < /dev/null > %v 2>&1 &", node.tmpLogFilePath)); err != nil {
		panic(err)
	}
	return
}

func (node *Node) Close() error {
	resp, err := node.client.Get(fmt.Sprintf("%v/close", node.endpoint))
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		bodyString, err := io.ReadAll(resp.Body)
		if err != nil {
			return err
		}
		return errors.New(string(bodyString))
	}
	time.Sleep(2 * time.Second)
	sshClient, err := ssh.Dial("tcp", fmt.Sprintf("%v:22", node.host), node.sshClientConfig)
	if err != nil {
		return err
	}
	defer sshClient.Close()
	session, err := sshClient.NewSession()
	if err != nil {
		return err
	}
	defer session.Close()
	return session.Run(fmt.Sprintf("rm -rf %v", node.tmpDirPath))
}

func (node *Node) Create(name string) string {
	response, err := node.client.Get(fmt.Sprintf("%v/program/create/%v", node.endpoint, name))
	if err != nil {
		panic(err)
	}
	defer response.Body.Close()
	responseBytes, err := io.ReadAll(response.Body)
	if err != nil {
		panic(err)
	}
	return string(responseBytes)
}

func (node *Node) UploadToPath(uuid, filePath, remotePath string) {
	file, err := os.Open(filePath)
	if err != nil {
		panic(err)
	}
	defer file.Close()
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)
	pathPart, err := writer.CreateFormField("path")
	if err != nil {
		panic(err)
	}
	if _, err := pathPart.Write([]byte(filepath.Dir(remotePath))); err != nil {
		panic(err)
	}
	filePart, err := writer.CreateFormFile("file", filepath.Base(remotePath))
	if err != nil {
		panic(err)
	}
	if _, err = io.Copy(filePart, file); err != nil {
		panic(err)
	}
	if err = writer.Close(); err != nil {
		panic(err)
	}
	response, err := node.client.Post(fmt.Sprintf("%v/program/upload/%v", node.endpoint, uuid), writer.FormDataContentType(), body)
	if err != nil {
		panic(err)
	}
	defer response.Body.Close()
	if response.StatusCode != 200 {
		responseBody, err := io.ReadAll(response.Body)
		if err != nil {
			panic(err)
		}
		log.Fatalln(string(responseBody))
	}
}

func (node *Node) Upload(uuid, localPath string) {
	node.UploadToPath(uuid, localPath, filepath.Base(localPath))
}

func (node *Node) Start(uuid, path, logFile string, args ...string) {
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
	response, err := node.client.Post(fmt.Sprintf("%v/program/start/%v", node.endpoint, uuid),
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
		log.Fatalln(responseString)
	}
}

func (node *Node) Status(uuid string) Status {
	response, err := node.client.Get(fmt.Sprintf("%v/program/status/%v", node.endpoint, uuid))
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
		log.Fatalln(responseString)
	}
	status, err := strconv.Atoi(responseString)
	if err != nil {
		panic(err)
	}
	return Status(status)
}

func (node *Node) Stop(uuid string) {
	response, err := node.client.Get(fmt.Sprintf("%v/program/stop/%v", node.endpoint, uuid))
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
		log.Fatalln(responseString)
	}
}

func (node *Node) Get(uuid, outputDirPath, config string, iteration int) {
	ip := strings.ReplaceAll(node.host, ".", "_")
	// TODO the node should receive the full output directory, and not create it itself
	configName := strings.TrimSuffix(strings.ReplaceAll(config, "-", "_"), ".conf")
	dirPath := filepath.Join(outputDirPath, fmt.Sprintf("i-%v-c-%v-%v-node-%v", iteration,
		configName, uuid, ip))
	if err := os.MkdirAll(dirPath, 0755); err != nil {
		panic(err)
	}
	response, err := node.client.Get(fmt.Sprintf("%v/program/get/%v", node.endpoint, uuid))
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
		filePath := filepath.Join(dirPath, f.Name)

		if !strings.HasPrefix(filePath, filepath.Clean(outputDirPath)+string(os.PathSeparator)) {
			panic(fmt.Sprintf("path join failed: %v\n", filePath))
		}
		if f.FileInfo().IsDir() {
			if err := os.MkdirAll(filePath, os.ModePerm); err != nil {
				panic(err)
			}
			continue
		}

		if err := os.MkdirAll(filepath.Dir(filePath), os.ModePerm); err != nil {
			panic(err)
		}

		dstFile, err := os.OpenFile(filePath, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, f.Mode())
		if err != nil {
			panic(err)
		}

		fileInArchive, err := f.Open()
		if err != nil {
			panic(err)
		}

		if _, err := io.Copy(dstFile, fileInArchive); err != nil {
			panic(err)
		}

		dstFile.Close()
		fileInArchive.Close()
	}
}
