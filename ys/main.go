package main

import (
	"archive/zip"
	"context"
	"fmt"
	"io"
	"io/fs"
	"io/ioutil"
	"log"
	"net"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"strings"
	"time"

	gonanoid "github.com/matoous/go-nanoid/v2"

	"github.com/gin-gonic/gin"

	"gopkg.in/alecthomas/kingpin.v2"

	"golang.org/x/crypto/ssh"

	"github.com/jdonkervliet/hocon"
)

var (
	inspect    = kingpin.Flag("inspect", "Halts execution before cleanup to allow for manual inspection.").Short('i').Bool()
	configPath = kingpin.Arg("configPath", "Path to configuration file.").String()
	isWorker   = kingpin.Flag("worker", "This node is a worker.").Short('w').Bool()
	port       = kingpin.Flag("port", "The worker port.").Short('p').Int()
)

type StartRequest struct {
	Command string   `json:"command"`
	Args    []string `json:"args"`
	LogFile string   `json:"logFile"`
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
	uuidProcessMap := make(map[string]Process)

	r := gin.Default()
	srv := &http.Server{
		Addr:    fmt.Sprintf(":%v", *port),
		Handler: r,
	}
	quit := make(chan os.Signal)
	signal.Notify(quit, os.Interrupt)

	r.GET("/ping", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"message": "pong",
		})
	})
	r.GET("/program/create/:name", func(c *gin.Context) {
		name := c.Param("name")
		id, err := gonanoid.Generate("1234567890abcdef", 8)
		if err != nil {
			c.AbortWithError(http.StatusInternalServerError, err)
			return
		}
		uuid := fmt.Sprintf("%v-%v", name, id)
		if err = os.MkdirAll(uuid, 0755); err != nil {
			c.AbortWithError(http.StatusInternalServerError, err)
			return
		}
		r.StaticFS(fmt.Sprintf("/program/dir/%v", uuid), http.Dir(fmt.Sprintf("./%v", uuid)))
		r.GET(fmt.Sprintf("/program/get/%v", uuid), func(c *gin.Context) {
			c.Writer.Header().Set("Content-type", "application/octet-stream")
			c.Writer.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename='%v.zip'", uuid))
			zipWriter := zip.NewWriter(c.Writer)
			defer zipWriter.Close()
			err := filepath.WalkDir(uuid, func(path string, d fs.DirEntry, err error) error {
				if err != nil {
					return err
				}
				if !d.IsDir() {
					relPath, err := filepath.Rel(uuid, path)
					if err != nil {
						return err
					}
					fileWriter, err := zipWriter.Create(relPath)
					if err != nil {
						return err
					}
					file, err := os.Open(path)
					if err != nil {
						return err
					}
					if _, err := io.Copy(fileWriter, file); err != nil {
						return err
					}
				}
				return nil
			})
			if err != nil {
				log.Printf("error while creating zip file: %v", err)
				c.AbortWithError(http.StatusInternalServerError, err)
				return
			}
		})
		c.String(http.StatusOK, uuid)
	})
	r.POST("/program/upload/:uuid", func(c *gin.Context) {
		uuid := c.Param("uuid")
		path := c.Request.FormValue("path")
		file, header, err := c.Request.FormFile("file")
		if err != nil {
			log.Println("request does not contain file")
			c.String(http.StatusBadRequest, fmt.Sprintf("file err : %s", err.Error()))
			return
		}
		filePath := filepath.Join(uuid, path, header.Filename)
		if err = os.MkdirAll(filepath.Dir(filePath), 0755); err != nil {
			log.Printf("could not create path at %v\n", filepath.Dir(filePath))
			c.AbortWithError(http.StatusInternalServerError, err)
			return
		}
		out, err := os.Create(filePath)
		if err != nil {
			log.Printf("could not create file at %v\n", filePath)
			c.AbortWithError(http.StatusInternalServerError, err)
			return
		}
		defer out.Close()
		_, err = io.Copy(out, file)
		if err != nil {
			panic(err)
		}
		c.JSON(http.StatusOK, gin.H{"filepath": filePath})
	})
	r.POST("/program/start/:uuid", func(c *gin.Context) {
		uuid := c.Param("uuid")
		var json StartRequest
		err := c.BindJSON(&json)
		if err != nil {
			c.AbortWithError(http.StatusBadRequest, err)
			return
		}
		file, err := os.Create(filepath.Join(uuid, json.LogFile))
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
		cmd.Dir = uuid
		if err = cmd.Start(); err != nil {
			c.AbortWithError(http.StatusInternalServerError, err)
		}
		process := Process{
			Command: cmd,
			LogFile: file,
		}
		uuidProcessMap[uuid] = process
		c.String(http.StatusOK, "started!")
	})
	r.GET("/program/status/:uuid", func(c *gin.Context) {
		uuid := c.Param("uuid")
		process, ok := uuidProcessMap[uuid]
		if !ok {
			c.AbortWithStatusJSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("unknown uuid: %v", uuid)})
			return
		}
		var status Status
		if process.Command != nil &&
			process.Command.ProcessState != nil &&
			process.Command.ProcessState.Exited() {
			status = Stopped
		} else {
			status = Running
		}
		c.JSON(http.StatusOK, status)
	})
	r.GET("/program/stop/:uuid", func(c *gin.Context) {
		uuid := c.Param("uuid")
		process, ok := uuidProcessMap[uuid]
		if !ok {
			c.AbortWithStatusJSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("unknown uuid: %v", uuid)})
			return
		}
		err := process.Command.Process.Signal(os.Interrupt)
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
		log.Println("stopping worker")
		go func() {
			time.Sleep(1 * time.Second)
			quit <- os.Interrupt
		}()
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

	gameNode := 0
	if game.NeedsNode() {
		gameNode = 1
	}

	numPlayerEmulation := config.GetInt("player-emulation.number-of-nodes")
	nodes, err := prov.Provision(gameNode + numPlayerEmulation)

	// TODO Deploy pecosa on game node
	if err = game.Deploy(nodes[0]); err != nil {
		panic(err)
	}

	playerEmulation := make([]Program, numPlayerEmulation)
	for i := 0; i < numPlayerEmulation; i++ {
		playerEmulation[i] = PlayerEmulationFromConfig(game.Host, game.Port, *configPath)
	}
	if err != nil {
		panic(err)
	}

	if err = game.Start(); err != nil {
		panic(err)
	}
	log.Println("game started, waiting 10 seconds to boot")
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
		if err := program.Stop(); err != nil {
			panic(err)
		}
	}
	if err = game.Stop(); err != nil {
		panic(err)
	}
	outputDir := config.GetString("directories.raw-output")
	if err := game.Get(outputDir, 0); err != nil {
		panic(err)
	}
	for _, program := range playerEmulation {
		if err := program.Get(outputDir, 0); err != nil {
			panic(err)
		}
	}

	if *inspect {
		log.Println("inspection mode enabled. Waiting for user input to continue")
		var input string
		fmt.Scanln(&input)
	}

	for _, node := range nodes {
		err := node.Close()
		if err != nil {
			log.Printf("error stopping node at %v: %v", node.ipAddress, err)
		}
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
