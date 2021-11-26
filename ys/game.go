package main

import (
	"bufio"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/gurkankaymak/hocon"
	gonanoid "github.com/matoous/go-nanoid/v2"
)

type Game interface {
	Architecture() string
	Address() string
	Program
}

type JarGame struct {
	*Jar
	host string
	port int
}

func (game *JarGame) Deploy(node *Node) error {
	// TODO support serverless game, uses an HTTP endpoint, port 443
	game.host = node.host
	game.port = 25565 // TODO prevent hard coding MC port
	return game.Jar.Deploy(node)
}

func (game *JarGame) Architecture() string {
	return "jar"
}

func (game *JarGame) Address() string {
	return fmt.Sprintf("%v:%v", game.host, game.port)
}

func GameFromConfig(basePath string, config *hocon.Config, rootConfigPath string) (Game, error) {
	archi := config.GetString("architecture")
	switch archi {
	case "jar":
		return gameFromJar(basePath, config)
	case "servo":
		return gameFromServo(config, rootConfigPath)
	default:
		return nil, errors.New(fmt.Sprintf("game architecture '%v' not supported", archi))
	}
}

func gameFromServo(config *hocon.Config, configPath string) (Game, error) {
	envParams := config.GetStringMapString("servo.environment")
	env := make([]string, len(envParams))
	i := 0
	for k, v := range envParams {
		env[i] = fmt.Sprintf("%v=%v", k, v)
		i++
	}
	return &ServoAWS{
		repo:   config.GetString("servo.build.git"),
		commit: config.GetString("servo.build.commit"),
		env:    env,
		config: configPath,
	}, nil
}

func gameFromJar(basePath string, config *hocon.Config) (*JarGame, error) {
	resources := config.GetArray("jar.resources")
	resourcesPaths := make([]LocalRemotePath, len(resources))
	for i, resource := range resources {
		local := resource.(hocon.Object)["local"].(hocon.String).String()
		remoteValue := resource.(hocon.Object)["remote"]
		var remote string
		if remoteValue != nil {
			remote = remoteValue.(hocon.String).String()
		} else {
			remote = ""
		}
		rel := filepath.Join(basePath, local)
		resourcesPaths[i] = LocalRemotePathFromStrings(rel, remote)
	}
	lrJarPath := LocalRemotePathFromConfig(basePath, config.GetConfig("jar.path"))
	if _, err := os.Stat(lrJarPath.LocalPath); errors.Is(err, os.ErrNotExist) {
		return nil, fmt.Errorf("game jar does not exist: %w", err)
	}
	return &JarGame{
		Jar: &Jar{
			name:         "mve",
			JarPath:      lrJarPath,
			JVMArgs:      config.GetStringSlice("jar.jvm.options"),
			JarArguments: config.GetStringSlice("jar.arguments"),
			Resources:    resourcesPaths,
		},
	}, nil
}

type ServoAWS struct {
	repo     string
	commit   string
	env      []string
	config   string
	Endpoint *url.URL
}

func (s *ServoAWS) Name() string {
	return "servo"
}

func (s *ServoAWS) NeedsNode() bool {
	return false
}

func (s *ServoAWS) Deploy(node *Node) error {
	id, err := gonanoid.Generate("1234567890abcdef", 8)
	tmpDir := filepath.Join("/tmp", fmt.Sprintf("servo-%v", id))

	// Clone Servo repo
	log.Printf("cloning servo into %v\n", tmpDir)
	gitCloneCmd := exec.Command("git", "clone", s.repo, tmpDir)
	if _, err := gitCloneCmd.Output(); err != nil {
		panic(err)
	}

	// Write application.conf for Servo to use
	bConfig, err := ioutil.ReadFile(s.config)
	if err != nil {
		panic(err)
	}
	if err := ioutil.WriteFile(filepath.Join(tmpDir, "application.conf"), bConfig, 0644); err != nil {
		panic(err)
	}

	// Checkout correct Servo commit
	gitCheckoutCmd := exec.Command("git", "checkout", s.commit)
	gitCheckoutCmd.Dir = tmpDir
	if _, err := gitCheckoutCmd.Output(); err != nil {
		panic(err)
	}

	deployScriptPath := filepath.Join(tmpDir, "deployment-scripts/aws/deploy")
	deployScriptDirPath := filepath.Dir(deployScriptPath)

	// Create and write deployment parameters file, read by deploy script
	paramsFilePath := filepath.Join(deployScriptDirPath, "deployment-parameters")
	if err := s.writeEnvToFile(paramsFilePath); err != nil {
		panic(err)
	}

	// Run deploy script
	servoDeployCmd := exec.Command(deployScriptPath)
	servoDeployCmd.Dir = tmpDir
	servoDeployCmd.Env = append(os.Environ(), s.env...)
	if output, err := servoDeployCmd.CombinedOutput(); err != nil {
		log.Println("something went wrong when deploying servo")
		log.Println(string(output))
		panic(err)
	}
	namingUrlFile, err := os.Open(filepath.Join(deployScriptDirPath, "stack.json"))
	if err != nil {
		panic(err)
	}
	defer namingUrlFile.Close()
	b, err := io.ReadAll(namingUrlFile)
	if err != nil {
		panic(err)
	}
	log.Println(string(b))
	var m map[string]interface{}
	json.Unmarshal(b, &m)
	message, ok := m["HttpApiUrl"]
	if !ok {
		panic("stack.json does not contain field 'HttpApiUrl'")
	}
	rawURL := message.(string)
	log.Println(rawURL)
	gameURL, err := url.Parse(fmt.Sprintf("%v/naming", strings.TrimSpace(rawURL)))
	if err != nil {
		panic(err)
	}
	s.Endpoint = gameURL
	log.Println(s.Endpoint)
	os.RemoveAll(tmpDir)
	return nil
}

func (s *ServoAWS) writeEnvToFile(paramsFilePath string) error {
	f, err := os.Create(paramsFilePath)
	if err != nil {
		return err
	}
	defer f.Close()
	// We also pass the variables through the environment. See `servoDeployCmd.Env` below
	w := bufio.NewWriter(f)
	defer w.Flush()
	for _, line := range s.env {
		if _, err = w.WriteString(line + "\n"); err != nil {
			return err
		}
	}
	return nil
}

func (s *ServoAWS) Start() error {
	// no need to start anything
	return nil
}

func (s *ServoAWS) Wait(timeout time.Duration) error {
	return errors.New("serverless app never ends")
}

func (s *ServoAWS) Stop() error {
	// no need to stop anything
	return nil
}

func (s *ServoAWS) Get(outputDirPath, prefix string) error {
	// TODO get metrics from servo
	return nil
}

func (s *ServoAWS) Architecture() string {
	return s.Name()
}

func (s *ServoAWS) Address() string {
	return s.Endpoint.String()
}
