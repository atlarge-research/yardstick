package main

import (
	"errors"
	"log"
	"time"

	"github.com/jdonkervliet/hocon"
)

type Provisioner interface {
	Provision(num int) ([]*Node, error)
}

type StaticProvisioner struct {
	ips   []string
	count int
}

func (p *StaticProvisioner) Provision(num int) ([]*Node, error) {
	if num > len(p.ips[p.count:]) {
		return nil, errors.New("insufficient nodes available")
	}
	addresses := p.ips[p.count : p.count+num]
	p.count += num
	nodes := make([]*Node, num)
	for i, address := range addresses {
		nodes[i] = NewNode(address)
	}
	// Wait for node server to become active
	// TODO make nicer
	time.Sleep(1 * time.Second)
	return nodes, nil
}

func ProvisionerFromConfig(config *hocon.Config) Provisioner {
	method := config.GetString("method")
	if method == "static" {
		ips := config.GetStringSlice("static.ips")
		return &StaticProvisioner{count: 0, ips: ips}
	}
	log.Fatalf("provisioning method '%v' not supported", method)
	return nil
}
