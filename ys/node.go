package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"mime/multipart"
	"net/http"
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
	ipAddress       string
	endpoint        string
	client          *http.Client
	sshClientConfig *ssh.ClientConfig
	tmpDirPath      string
	tmpFilePath     string
	tmpLogFilePath  string
}

func NewNode(ipAddress string) (node *Node) {
	node = &Node{}
	node.ipAddress = ipAddress
	node.endpoint = fmt.Sprintf("http://%v:8080", ipAddress)
	node.client = &http.Client{Timeout: 10 * time.Second}

	// Prepare SSH authentication
	// FIXME from configPath
	key := readPubKey("/Users/jesse/.ssh/id_rsa")
	node.sshClientConfig = &ssh.ClientConfig{
		// FIXME from configPath
		User: "jesse",
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
	node.tmpFilePath = path.Join(node.tmpDirPath, "deploy")
	node.tmpLogFilePath = path.Join(node.tmpDirPath, "deploy.log")

	// Use SSH client to create SFTP client
	sftpClient, err := sftp.NewClient(sshClient)
	if err != nil {
		panic(err)
	}
	defer sftpClient.Close()

	// Open tmp file on remote
	dstFile, err := sftpClient.Create(node.tmpFilePath)
	if err != nil {
		panic(err)
	}
	defer dstFile.Close()

	// TODO make it work if the remote architecture is not the local architecture
	// Open current binary file
	exe, err := os.Executable()
	if err != nil {
		panic(err)
	}
	srcFile, err := os.Open(exe)
	if err != nil {
		panic(err)
	}
	defer srcFile.Close()

	// Write current binary into remote tmp file
	if _, err := dstFile.ReadFrom(srcFile); err != nil {
		panic(err)
	}

	// Make remote tmp file executable and run it
	session, err := sshClient.NewSession()
	defer session.Close()
	if err := session.Start(
		fmt.Sprintf("cd %v &&", node.tmpDirPath) +
			fmt.Sprintf(" chmod +x %v &&", node.tmpFilePath) +
			fmt.Sprintf(" nohup %v --worker", node.tmpFilePath) +
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
	sshClient, err := ssh.Dial("tcp", fmt.Sprintf("%v:22", node.ipAddress), node.sshClientConfig)
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

func (node *Node) UploadToPath(filePath, remotePath string) {
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
	response, err := node.client.Post(fmt.Sprintf("%v/upload", node.endpoint), writer.FormDataContentType(), body)
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

func (node *Node) Upload(localPath string) {
	node.UploadToPath(localPath, filepath.Base(localPath))
}

func (node *Node) Start(path, logFile string, args ...string) int {
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
	response, err := node.client.Post(fmt.Sprintf("%v/start", node.endpoint),
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
	res, err := strconv.Atoi(responseString)
	if err != nil {
		panic(err)
	}
	return res
}

func (node *Node) Status(pid int) Status {
	body, err := json.Marshal(map[string]int{"pid": pid})
	if err != nil {
		panic(err)
	}
	response, err := node.client.Post(fmt.Sprintf("%v/status", node.endpoint), "application/json", bytes.NewBuffer(body))
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

func (node *Node) Stop(pid int) {
	body, err := json.Marshal(map[string]int{"pid": pid})
	if err != nil {
		panic(err)
	}
	response, err := node.client.Post(fmt.Sprintf("%v/stop", node.endpoint), "application/json", bytes.NewBuffer(body))
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

func (node *Node) Get() {
	// FIXME implement
}
