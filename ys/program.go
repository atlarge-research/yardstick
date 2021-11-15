package main

import (
	"errors"
	"path/filepath"
	"strings"
	"time"

	"github.com/jdonkervliet/hocon"

	"github.com/schollz/progressbar/v3"
)

type Program interface {
	NeedsNode() bool
	Deploy(node *Node) error
	Start() error
	Wait(timeout time.Duration) error
	Stop() error
	Logs() error
	Status() error
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
	rel, err := filepath.Rel(basePath, local)
	if err != nil {
		panic(err)
	}
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
	node         *Node
	JarPath      LocalRemotePath
	JarArguments []string
	JVMArgs      []string
	Resources    []LocalRemotePath
	jarPID       int
}

func (jar *Jar) NeedsNode() bool {
	return true
}

func (jar *Jar) Deploy(node *Node) error {
	jar.node = node
	bar := progressbar.Default(int64(1+len(jar.Resources)), "deploying jar")
	jar.node.UploadToPath(jar.JarPath.LocalPath, jar.JarPath.RemotePath)
	bar.Add(1)
	for _, resource := range jar.Resources {
		jar.node.UploadToPath(resource.LocalPath, resource.RemotePath)
		bar.Add(1)
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
	jar.jarPID = jar.node.Start("java", remoteLogFilePath, args...)
	return
}

func (jar *Jar) Wait(timeout time.Duration) error {
	if jar.jarPID == 0 {
		return errors.New("program not started")
	}
	stopped := make(chan bool)
	go func() {
		for {
			status := jar.node.Status(jar.jarPID)
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
	jar.node.Stop(jar.jarPID)
	return
}

// FIXME implement
func (jar *Jar) Logs() (err error) {
	jar.node.Get()
	return
}

// FIXME implement some kind of status
func (jar *Jar) Status() (err error) {
	return
}
