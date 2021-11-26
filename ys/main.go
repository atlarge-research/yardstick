package main

import (
	"archive/zip"
	"context"
	"fmt"
	"io"
	"io/fs"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/gurkankaymak/hocon"
	gonanoid "github.com/matoous/go-nanoid/v2"
	"github.com/schollz/progressbar/v3"

	"github.com/gin-gonic/gin"

	"gopkg.in/alecthomas/kingpin.v2"

	"golang.org/x/crypto/ssh"
)

const defaultConfig = "default"

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
		panic(err)
	}
	log.Println("Server exiting")
}

type ExperimentConfig struct {
	Name string
	Path string
}

func primary() {
	conf, err := hocon.ParseResource(*configPath)
	if err != nil {
		log.Fatal("error while reading configPath: ", err)
	}

	configDirPath := conf.GetString("yardstick.directories.configs")
	configDir, err := os.Open(configDirPath)
	if err != nil {
		panic(err)
	}
	configDirEntries, err := configDir.ReadDir(0)
	if err != nil {
		panic(err)
	}
	configFiles := make([]ExperimentConfig, 0)
	for _, f := range configDirEntries {
		if !f.IsDir() && strings.HasSuffix(f.Name(), ".conf") {
			iterationConf := filepath.Join(configDirPath, f.Name())
			tempConf, err := mergeConfFiles(*configPath, iterationConf)
			if err != nil {
				panic(err)
			}
			configFiles = append(configFiles, ExperimentConfig{
				Name: strings.TrimSuffix(filepath.Base(f.Name()), ".conf"),
				Path: tempConf,
			})
		}
	}
	if len(configFiles) == 0 {
		configFiles = append(configFiles, ExperimentConfig{
			Name: defaultConfig,
			Path: *configPath,
		})
	}
	defer func() {
		for _, cf := range configFiles {
			if cf.Name != defaultConfig {
				os.RemoveAll(cf.Path)
			}
		}
	}()

	log.Println(conf)
	var totalIterations int64
	for _, c := range configFiles {
		parsedConf, err := hocon.ParseResource(c.Path)
		if err != nil {
			panic(err)
		}
		totalIterations += int64(parsedConf.GetInt("yardstick.iterations"))
	}
	bar := progressbar.Default(totalIterations, "running experiment")
	go func() {
		// See https://github.com/schollz/progressbar/issues/81
		time.Sleep(4 * time.Second)
		bar.RenderBlank()
	}()
	for _, c := range configFiles {
		parsedConf, err := hocon.ParseResource(c.Path)
		if err != nil {
			panic(err)
		}
		for i := 0; i < parsedConf.GetInt("yardstick.iterations"); i++ {
			ResetPort()
			if err := runExperimentIteration(c, i); err != nil {
				panic(err)
			}
			bar.Add(1)
		}
	}
	runDataScripts(conf.GetConfig("yardstick.directories"))
}

func mergeConfFiles(base string, others ...string) (string, error) {
	tmpFile, err := os.CreateTemp("", "")
	if err != nil {
		return "", err
	}
	defer tmpFile.Close()
	if err := writeFromFile(tmpFile, base); err != nil {
		return "", err
	}
	if _, err := tmpFile.WriteString("\n"); err != nil {
		return "", err
	}
	for _, other := range others {
		if err := writeFromFile(tmpFile, other); err != nil {
			return "", err
		}
		if _, err := tmpFile.WriteString("\n"); err != nil {
			return "", err
		}
	}
	return tmpFile.Name(), nil
}

func writeFromFile(w io.Writer, path string) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = io.Copy(w, f)
	return err
}

func runExperimentIteration(expConfig ExperimentConfig, iteration int) error {
	config, err := hocon.ParseResource(expConfig.Path)
	if err != nil {
		return err
	}
	outputDir := config.GetString("yardstick.directories.raw-output")
	configName := strings.TrimSuffix(strings.ReplaceAll(expConfig.Name, "-", "_"), ".conf")
	prefix := fmt.Sprintf("i-%v-c-%v", iteration, configName)
	entries, err := os.ReadDir(outputDir)
	if err != nil {
		return fmt.Errorf("could not read output dir: %w", err)
	}
	for _, entry := range entries {
		if strings.HasPrefix(entry.Name(), prefix) {
			log.Printf("directory with prefix %v exists. Skipping...\n", prefix)
			return nil
		}
	}

	inputDirectoryPath := config.GetString("yardstick.directories.input")
	prov, err := ProvisionerFromConfig(config.GetConfig("yardstick.provisioning"), inputDirectoryPath)
	if err != nil {
		return fmt.Errorf("could not create provisioner: %w", err)
	}
	game, err := GameFromConfig(inputDirectoryPath, config.GetConfig("yardstick.game"), expConfig.Path)
	if err != nil {
		return fmt.Errorf("could not create game: %w", err)
	}

	basePort := 8080
	var gameNode *Node
	if game.NeedsNode() {
		nodes, err := prov.Provision(1, basePort)
		if err != nil {
			return fmt.Errorf("could not provision nodes: %w", err)
		}
		gameNode = nodes[0]
	}

	if gameNode != nil {
		basePort++
	}
	numPlayerEmulation := config.GetInt("yardstick.player-emulation.number-of-nodes")
	playerEmulationNodes, err := prov.Provision(numPlayerEmulation, basePort)

	// TODO Deploy pecosa on game node
	if err = game.Deploy(gameNode); err != nil {
		return fmt.Errorf("could not deploy game: %w", err)
	}

	playerEmulation := make([]Program, numPlayerEmulation)
	for i := 0; i < numPlayerEmulation; i++ {
		pe, err := PlayerEmulationFromConfig(game.Address(), expConfig.Path, i)
		if err != nil {
			return fmt.Errorf("could not create player emulation from config %v: %w", config, err)
		}
		playerEmulation[i] = pe
	}

	if err = game.Start(); err != nil {
		return fmt.Errorf("could not start game: %w", err)
	}
	log.Println("game started, waiting 10 seconds to boot")
	time.Sleep(10 * time.Second)

	for i, program := range playerEmulation {
		// TODO Deploy pecosa on this node
		err = program.Deploy(playerEmulationNodes[i])
		if err != nil {
			return fmt.Errorf("could not deploy player emulation: %w", err)
		}
	}

	log.Println("starting player emulation")
	for _, program := range playerEmulation {
		err = program.Start()
		if err != nil {
			return fmt.Errorf("could not start player emulation: %w", err)
		}
	}

	log.Println("waiting for player emulation to finish")
	var wg sync.WaitGroup
	for _, program := range playerEmulation {
		wg.Add(1)
		program := program
		go func() {
			program.Wait(config.GetDuration("yardstick.player-emulation.arguments.duration") + 1*time.Minute)
			wg.Done()
		}()
	}
	wg.Wait()

	log.Println("stopping player emulation")
	for _, program := range playerEmulation {
		if err := program.Stop(); err != nil {
			return fmt.Errorf("could not stop player emulation: %w", err)
		}
	}

	log.Println("stopping mve")
	if err = game.Stop(); err != nil {
		return fmt.Errorf("could not stop game: %w", err)
	}

	log.Println("downloading mve output")
	if err := game.Get(outputDir, prefix); err != nil {
		return fmt.Errorf("could not get game data: %w", err)
	}
	log.Println("downloading player emulation output")
	for _, program := range playerEmulation {
		if err := program.Get(outputDir, prefix); err != nil {
			return fmt.Errorf("could not get player emulation data: %w", err)
		}
	}

	if *inspect {
		log.Println("inspection mode enabled. Waiting for user input to continue")
		var input string
		fmt.Scanln(&input)
	}

	log.Println("stopping workers")
	if gameNode != nil {
		if err := gameNode.Close(); err != nil {
			return fmt.Errorf("could not close game: %w", err)
		}
	}
	for _, node := range playerEmulationNodes {
		err := node.Close()
		if err != nil {
			log.Printf("error stopping node at %v: %v", node.host, err)
		}
	}
	return nil
}

func runDataScripts(config *hocon.Config) {
	inputDir := config.GetString("raw-output")
	scriptsDir := config.GetString("raw-output-scripts")
	outputDir := config.GetString("output")
	scripts, err := os.Open(scriptsDir)
	if err != nil {
		panic(err)
	}
	entries, err := scripts.ReadDir(0)
	if err != nil {
		panic(err)
	}
	for _, f := range entries {
		scriptPath := filepath.Join(scriptsDir, f.Name())
		command := exec.Command(scriptPath, inputDir, outputDir)
		log.Println(command)
		command.Run()
	}
}

func main() {
	kingpin.Parse()
	if *isWorker {
		log.Println("worker")
		worker()
	} else {
		log.Println("primary")
		primary()
	}
}
