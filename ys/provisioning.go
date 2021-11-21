package main

import (
	"errors"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/jdonkervliet/hocon"
)

type Provisioner interface {
	Provision(num, basePort int) ([]*Node, error)
	Close()
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
		nodes[i] = NewNode(p.user, address, "", p.workerBinaryPath)
	}
	// Wait for node server to become active
	// TODO make nicer
	time.Sleep(1 * time.Second)
	return nodes, nil
}

func (p *StaticProvisioner) Close() {
	// Do nothing
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
	} else if method == "das5" {
		user := config.GetString("das5.user")
		if user == "" {
			panic("user cannot be empty")
		}
		host := config.GetString("das5.host")
		if host == "" {
			panic("das5 address cannot be empty")
		}
		return &DAS5Provisioner{
			user:             user,
			host:             host,
			workerBinaryPath: filepath.Join(inputDirectoryPath, binary),
		}
	}
	log.Fatalf("provisioning method '%v' not supported", method)
	return nil
}

type DAS5Provisioner struct {
	host             string
	user             string
	workerBinaryPath string
	reservations     []string
}

func (das *DAS5Provisioner) Provision(num, basePort int) ([]*Node, error) {
	seconds := 900 // 15 minute max runtime
	cmd := exec.Command("ssh", fmt.Sprintf("%v@%v", das.user, das.host), "preserve", "-np",
		strconv.Itoa(num), "-t", strconv.Itoa(seconds))
	b, err := cmd.CombinedOutput()
	if err != nil {
		return nil, err
	}
	fields := strings.Fields(strings.Split(string(b), "\n")[0])
	reservationNumber := strings.TrimSuffix(fields[len(fields)-1], ":")
	if err := waitForReservationReady(das.host, das.user, reservationNumber); err != nil {
		return nil, err
	}
	reservationFields, err := getReservation(das.host, das.user, reservationNumber)
	if err != nil {
		return nil, err
	}
	nodeAddresses := reservationFields[8:]
	if das.reservations == nil {
		das.reservations = make([]string, 0)
	}
	das.reservations = append(das.reservations, reservationNumber)
	nodes := make([]*Node, num)
	for i, address := range nodeAddresses {
		node := NewNode(das.user, address, das.host, das.workerBinaryPath)
		if err != nil {
			return nil, err
		}
		nodes[i] = node
	}
	time.Sleep(1 * time.Second)
	return nodes, nil
}

func waitForReservationReady(host, user, reservationNumber string) error {
	for {
		fields, err := getReservation(host, user, reservationNumber)
		if err != nil {
			return err
		}
		if len(fields) < 7 {
			return errors.New("invalid reservation: " + strings.Join(fields, " "))
		}
		if fields[6] == "R" {
			return nil // Ready!
		}
		time.Sleep(5 * time.Second)
	}
}

func getReservation(host, user, reservationNumber string) ([]string, error) {
	cmd := exec.Command("ssh", fmt.Sprintf("%v@%v", user, host), "preserve", "-llist")
	out, err := cmd.CombinedOutput()
	if err != nil {
		return nil, err
	}
	lines := string(out)
	for _, line := range strings.Split(lines, "\n") {
		fields := strings.Fields(line)
		if len(fields) > 1 {
			if fields[0] == reservationNumber && fields[1] == user {
				return fields, nil
			}
		}
	}
	return nil, errors.New("could not find reservation " + reservationNumber)
}

func (das *DAS5Provisioner) Close() {
	for _, reservation := range das.reservations {
		cmd := exec.Command("ssh", fmt.Sprintf("%v@%v", das.user, das.host), "preserve", "-c", reservation)
		cmd.Run()
	}
}
