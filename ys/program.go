package main

import (
	"errors"
	"path/filepath"
	"strings"
	"time"

	"github.com/jdonkervliet/hocon"
)

type Program interface {
	Name() string
	NeedsNode() bool
	Deploy(node *Node) error
	Start() error
	Wait(timeout time.Duration) error
	Stop() error
	Get(outputDirPath string, iteration int) error
}

type Status int

const (
	Running Status = iota
	Stopped
)

type LocalRemotePath struct {
	LocalPath  string
	RemotePath string
}

func LocalRemotePathFromConfig(basePath string, config *hocon.Config) (path LocalRemotePath) {
	local := config.GetString("local")
	remote := config.GetString("remote")
	rel := filepath.Join(basePath, local)
	path = LocalRemotePathFromStrings(rel, remote)
	return
}

func LocalRemotePathFromStrings(local, remote string) (path LocalRemotePath) {
	path.LocalPath = local
	if remote == "" {
		remote = filepath.Base(path.LocalPath)
	}
	path.RemotePath = remote
	return
}

type Jar struct {
	name         string
	uuid         string
	node         *Node
	JarPath      LocalRemotePath
	JarArguments []string
	JVMArgs      []string
	Resources    []LocalRemotePath
}

func (jar *Jar) Name() string {
	return jar.name
}

func (jar *Jar) NeedsNode() bool {
	return true
}

func (jar *Jar) Deploy(node *Node) error {
	jar.node = node
	jar.uuid = jar.node.Create(jar.Name())
	jar.node.UploadToPath(jar.uuid, jar.JarPath.LocalPath, jar.JarPath.RemotePath)
	for _, resource := range jar.Resources {
		jar.node.UploadToPath(jar.uuid, resource.LocalPath, resource.RemotePath)
	}
	return nil
}

func (jar *Jar) Start() (err error) {
	remoteLogFilePath := strings.TrimSuffix(jar.JarPath.RemotePath, ".jar") + ".log"
	args := make([]string, 0)
	args = append(args, jar.JVMArgs...)
	args = append(args, "-jar")
	args = append(args, jar.JarPath.RemotePath)
	args = append(args, jar.JarArguments...)
	jar.node.Start(jar.uuid, "java", remoteLogFilePath, args...)
	return
}

func (jar *Jar) Wait(timeout time.Duration) error {
	stopped := make(chan bool)
	go func() {
		for {
			status := jar.node.Status(jar.uuid)
			if status == Stopped {
				stopped <- true
				break
			}
			time.Sleep(1 * time.Second)
		}
	}()
	select {
	case <-stopped:
		return nil
	case <-time.After(timeout):
		return errors.New("player emulation timed out")
	}
}

func (jar *Jar) Stop() (err error) {
	jar.node.Stop(jar.uuid)
	return
}

func (jar *Jar) Get(outputDirPath string, iteration int) error {
	jar.node.Get(jar.uuid, outputDirPath, iteration)
	return nil
}
