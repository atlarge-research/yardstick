package main

import (
	"bufio"
	"bytes"
	"errors"
	"fmt"
	"log"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"time"

	"github.com/jdonkervliet/hocon"
)

type Game interface {
	Architecture() string
	Host() string
	Port() int
	Program
}

type JarGame struct {
	*Jar
	host string
	port int
}

func (game *JarGame) Deploy(node *Node) error {
	// TODO support serverless game, uses an HTTP endpoint, port 443
	game.host = node.ipAddress
	game.port = 25565 // TODO prevent hard coding MC port
	return game.Jar.Deploy(node)
}

func (game *JarGame) Architecture() string {
	return "jar"
}

func (game *JarGame) Host() string {
	return game.host
}

func (game *JarGame) Port() int {
	return game.port
}

func GameFromConfig(basePath string, config *hocon.Config) Game {
	archi := config.GetString("architecture")
	switch archi {
	case "jar":
		return gameFromJar(basePath, config)
	case "servo":
		return gameFromServo(config)
	default:
		log.Fatalf("game architecture '%v' not supported\n", archi)
	}
	return nil
}

func gameFromServo(config *hocon.Config) Game {
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
	}
}

func gameFromJar(basePath string, config *hocon.Config) *JarGame {
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
	return &JarGame{
		Jar: &Jar{
			name:         "mve",
			JarPath:      LocalRemotePathFromConfig(basePath, config.GetConfig("jar.path")),
			JVMArgs:      config.GetStringSlice("jar.jvm.options"),
			JarArguments: config.GetStringSlice("jar.arguments"),
			Resources:    resourcesPaths,
		},
	}
}

type ServoAWS struct {
	repo     string
	commit   string
	env      []string
	Endpoint *url.URL
}

func (s *ServoAWS) Name() string {
	return "servo"
}

func (s *ServoAWS) NeedsNode() bool {
	return false
}

func (s *ServoAWS) Deploy(node *Node) error {
	tmpDir, err := os.MkdirTemp("", "")
	if err != nil {
		panic(err)
	}
	if _, err := exec.Command("git", "clone", s.repo, tmpDir).Output(); err != nil {
		panic(err)
	}
	checkoutCmd := exec.Command("git", "checkout", s.commit)
	checkoutCmd.Dir = tmpDir
	if _, err := checkoutCmd.Output(); err != nil {
		panic(err)
	}
	deployScriptPath := filepath.Join(tmpDir, "deployment-scripts/aws/deploy")
	fmt.Println(deployScriptPath)
	cmd := exec.Command(deployScriptPath)
	cmd.Dir = filepath.Dir(deployScriptPath)
	env := make([]string, 0)
	env = append(env, s.env...)
	f, err := os.Create(filepath.Join(filepath.Dir(deployScriptPath), "deployment-parameters"))
	if err != nil {
		panic(err)
	}
	defer f.Close()
	w := bufio.NewWriter(f)
	defer w.Flush()
	for _, line := range env {
		_, _ = w.WriteString(line + "\n")
	}
	buf := &bytes.Buffer{}
	cmd.Stdout = buf
	cmd.Stderr = buf
	if err := cmd.Start(); err != nil {
		panic(err)
	}
	scanner := bufio.NewScanner(buf)
	re := regexp.MustCompile(`\s*POST\s+-\s+(https://.+)$`)
	for scanner.Scan() {
		line := string(scanner.Bytes())
		if s.Endpoint != nil {
			// endpoint already set, but keep scanning to process command output
			continue
		}
		matches := re.FindStringSubmatch(line)
		if len(matches) == 2 {
			gameURL, err := url.Parse(matches[1])
			if err != nil {
				panic(err)
			}
			s.Endpoint = gameURL
		}
	}
	if err := cmd.Wait(); err != nil {
		panic(err)
	}
	os.RemoveAll(tmpDir)
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

func (s *ServoAWS) Get(outputDirPath, config string, iteration int) error {
	// TODO get metrics from servo
	return nil
}

func (s *ServoAWS) Architecture() string {
	return s.Name()
}

func (s *ServoAWS) Host() string {
	return s.Endpoint.Hostname()
}

func (s *ServoAWS) Port() int {
	port, err := strconv.Atoi(s.Endpoint.Port())
	if err != nil {
		panic(err)
	}
	return port
}
