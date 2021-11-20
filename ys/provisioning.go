package main

import (
	"errors"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/jdonkervliet/hocon"
)

type Provisioner interface {
	Provision(num, basePort int) ([]*Node, error)
}

type StaticProvisioner struct {
	user             string
	key              string
	ips              []string
	count            int
	workerBinaryPath string
}

func (p *StaticProvisioner) Provision(num, basePort int) ([]*Node, error) {
	if num > len(p.ips[p.count:]) {
		return nil, errors.New("insufficient nodes available")
	}
	addresses := p.ips[p.count : p.count+num]
	p.count += num
	nodes := make([]*Node, num)
	for i, address := range addresses {
		port := basePort + i
		nodes[i] = NewNode(p.user, p.key, address, port, p.workerBinaryPath)
	}
	// Wait for node server to become active
	// TODO make nicer
	time.Sleep(1 * time.Second)
	return nodes, nil
}

func ProvisionerFromConfig(config *hocon.Config, inputDirectoryPath string) Provisioner {
	method := config.GetString("method")
	binary := config.GetString("worker-binary")
	if binary == "" {
		panic("cannot find worker binary")
	}
	if method == "static" {
		user := config.GetString("static.user")
		if user == "" {
			panic("user cannot be empty")
		}
		key := config.GetString("static.key")
		if key == "" {
			panic("key cannot be empty")
		}
		if _, err := os.Stat(key); errors.Is(err, os.ErrNotExist) {
			panic(err)
		}
		ips := config.GetStringSlice("static.ips")
		return &StaticProvisioner{count: 0, user: user, key: key, ips: ips, workerBinaryPath: filepath.Join(inputDirectoryPath, binary)}
	}
	log.Fatalf("provisioning method '%v' not supported", method)
	return nil
}
