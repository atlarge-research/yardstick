package main

import (
	"context"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"gopkg.in/alecthomas/kingpin.v2"

	"golang.org/x/crypto/ssh"

	"github.com/jdonkervliet/hocon"
)

var (
	configPath = kingpin.Arg("configPath", "Path to configuration file.").String()
	isWorker   = kingpin.Flag("worker", "This node is a worker.").Short('w').Bool()
)

type StartRequest struct {
	Command string   `json:"command"`
	Args    []string `json:"args"`
	LogFile string   `json:"logFile"`
}

type StopRequest struct {
	Pid int `json:"pid"`
}

func readPubKey(file string) ssh.AuthMethod {
	var key ssh.Signer
	var b []byte
	b, err := ioutil.ReadFile(file)
	if err != nil {
		panic(err)
	}
	if !strings.Contains(string(b), "ENCRYPTED") {
		key, _ = ssh.ParsePrivateKey(b)
	} else {
		key, _ = ssh.ParsePrivateKeyWithPassphrase(b, []byte(""))
	}
	return ssh.PublicKeys(key)
}

type Process struct {
	Command *exec.Cmd
	LogFile *os.File
}

func worker() {
	pidMap := make(map[int]Process)
	pid := 1

	r := gin.Default()
	srv := &http.Server{
		Addr:    ":8080",
		Handler: r,
	}
	quit := make(chan os.Signal)
	signal.Notify(quit, os.Interrupt)

	r.GET("/ping", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"message": "pong",
		})
	})
	r.POST("/upload", func(c *gin.Context) {
		file, header, err := c.Request.FormFile("file")
		if err != nil {
			c.String(http.StatusBadRequest, fmt.Sprintf("file err : %s", err.Error()))
			return
		}
		filename := header.Filename
		out, err := os.Create(filename)
		if err != nil {
			panic(err)
		}
		defer out.Close()
		_, err = io.Copy(out, file)
		if err != nil {
			panic(err)
		}
		c.JSON(http.StatusOK, gin.H{"filepath": filename})
	})
	r.POST("/start", func(c *gin.Context) {
		var json StartRequest
		err := c.BindJSON(&json)
		if err != nil {
			c.AbortWithError(http.StatusBadRequest, err)
			return
		}
		file, err := os.Create(json.LogFile)
		if err != nil {
			c.AbortWithError(http.StatusInternalServerError, err)
			return
		}
		formattedCommand := make([]string, 1)
		formattedCommand[0] = json.Command
		formattedCommand = append(formattedCommand, json.Args...)
		log.Printf("running command: %v\n", formattedCommand)
		cmd := exec.Command(json.Command, json.Args...)
		cmd.Stdout = file
		cmd.Stderr = file
		if err = cmd.Start(); err != nil {
			c.AbortWithError(http.StatusInternalServerError, err)
		}
		pid += 1
		process := Process{
			Command: cmd,
			LogFile: file,
		}
		pidMap[pid] = process
		c.JSON(http.StatusOK, pid)
	})
	r.POST("/status", func(c *gin.Context) {
		var json StopRequest
		err := c.BindJSON(&json)
		if err != nil {
			log.Println("stop received invalid request")
			c.AbortWithError(http.StatusBadRequest, err)
			return
		}
		process, ok := pidMap[json.Pid]
		if !ok {
			c.AbortWithStatusJSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("unknown pid: %v", json.Pid)})
			return
		}
		var status Status
		if process.Command.ProcessState.Exited() {
			status = Stopped
		} else {
			status = Running
		}
		c.JSON(http.StatusOK, status)
	})
	r.POST("/stop", func(c *gin.Context) {
		var json StopRequest
		err := c.BindJSON(&json)
		if err != nil {
			log.Println("stop received invalid request")
			c.AbortWithError(http.StatusBadRequest, err)
			return
		}
		process, ok := pidMap[json.Pid]
		if !ok {
			c.AbortWithStatusJSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("unknown pid: %v", json.Pid)})
			return
		}
		err = process.Command.Process.Signal(os.Interrupt)
		if err != nil {
			log.Println("something went wrong interrupting the process")
			c.AbortWithError(http.StatusInternalServerError, err)
			return
		}
		channel := make(chan error, 1)
		go func() {
			channel <- process.Command.Wait()
		}()
		select {
		case <-channel:
		case <-time.After(5 * time.Second):
			log.Println("why won't you die, mr. bond?")
			err = process.Command.Process.Kill()
		}
		if err != nil {
			log.Println("kill gave an error")
			c.AbortWithError(http.StatusInternalServerError, err)
			return
		}
		process.LogFile.Close()
	})
	r.GET("/close", func(c *gin.Context) {
		log.Println("stopping working")
		go func() {
			time.Sleep(1 * time.Second)
			quit <- os.Interrupt
		}()
	})
	r.POST("/get", func(c *gin.Context) {
		// FIXME allow file download (logs)
	})

	go func() {
		// service connections
		if err := srv.ListenAndServe(); err != nil {
			log.Printf("listen: %s\n", err)
		}
	}()

	// Wait for a signal to shut down
	<-quit

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		log.Fatal("Server Shutdown:", err)
	}
	log.Println("Server exiting")
}

func primary() {
	conf, err := hocon.ParseResource(*configPath)
	if err != nil {
		log.Fatal("error while reading configPath: ", err)
	}
	fmt.Println(conf)

	config := conf.GetConfig("benchmark")
	prov := ProvisionerFromConfig(config.GetConfig("provisioning"))
	game := GameFromConfig(config.GetString("directories.input"), config.GetConfig("game"))
	numPlayerEmulation := config.GetInt("player-emulation.number-of-nodes")
	playerEmulation := make([]Program, numPlayerEmulation)
	for i := 0; i < numPlayerEmulation; i++ {
		playerEmulation[i] = PlayerEmulationFromConfig(game.Endpoint, *configPath)
	}
	gameNode := 0
	if game.NeedsNode() {
		gameNode = 1
	}
	nodes, err := prov.Provision(gameNode + numPlayerEmulation)
	defer func() {
		for _, node := range nodes {
			err := node.Close()
			if err != nil {
				log.Printf("error stopping node at %v: %v", node.ipAddress, err)
			}
		}
	}()
	if err != nil {
		panic(err)
	}
	// TODO Deploy pecosa on game node
	if err = game.Deploy(nodes[0]); err != nil {
		panic(err)
	}
	if err = game.Start(); err != nil {
		panic(err)
	}
	time.Sleep(10 * time.Second)
	for i, program := range playerEmulation {
		// TODO Deploy pecosa on this node
		err = program.Deploy(nodes[1+i])
		if err != nil {
			panic(err)
		}
	}
	for _, program := range playerEmulation {
		err = program.Start()
		if err != nil {
			panic(err)
		}
	}
	for _, program := range playerEmulation {
		program.Wait(config.GetDuration("player-emulation.arguments.duration") + 1*time.Minute)
	}
	for _, program := range playerEmulation {
		err = program.Stop()
		if err != nil {
			panic(err)
		}
	}
	if err = game.Stop(); err != nil {
		panic(err)
	}
	for _, node := range nodes {
		node.Get()
	}
}

func handle(client net.Conn, sshClient *ssh.Client, remoteAddr string) {
	remote, err := sshClient.Dial("tcp", remoteAddr)
	if err != nil {
		panic(err)
	}
	defer remote.Close()

	defer client.Close()
	chDone := make(chan bool)

	// Start remote -> local data transfer
	go func() {
		_, err := io.Copy(client, remote)
		if err != nil {
			log.Println("error while copy remote->local:", err)
		}
		chDone <- true
	}()

	// Start local -> remote data transfer
	go func() {
		_, err := io.Copy(remote, client)
		if err != nil {
			log.Println(err)
		}
		chDone <- true
	}()

	<-chDone
}

func main() {
	kingpin.Parse()
	if *isWorker {
		fmt.Println("worker")
		worker()
	} else {
		fmt.Println("primary")
		primary()
	}
}
