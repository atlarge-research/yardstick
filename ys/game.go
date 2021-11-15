package main

import (
	"fmt"
	"log"
	"net/url"
	"path/filepath"

	"github.com/jdonkervliet/hocon"
)

type Game struct {
	Program
	Endpoint *url.URL
}

func (game *Game) Deploy(node *Node) error {
	// TODO support serverless game, uses an HTTP endpoint, port 443
	// TODO avoid hard coding Minecraft port
	gameURL, err := url.Parse(fmt.Sprintf("tcp://%v:25565", node.ipAddress))
	if err != nil {
		return err
	}
	game.Endpoint = gameURL
	return game.Program.Deploy(node)
}

func GameFromConfig(basePath string, config *hocon.Config) *Game {
	archi := config.GetString("architecture")
	switch archi {
	case "jar":
		resources := config.GetArray("resources")
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
			rel, err := filepath.Rel(basePath, local)
			if err != nil {
				panic(err)
			}
			resourcesPaths[i] = LocalRemotePathFromStrings(rel, remote)
		}
		return &Game{
			Program: &Jar{
				JarPath:      LocalRemotePathFromConfig(basePath, config.GetConfig("jar.path")),
				JVMArgs:      config.GetStringSlice("jar.jvm.options"),
				JarArguments: config.GetStringSlice("jar.arguments"),
				Resources:    resourcesPaths,
			},
		}
	default:
		log.Fatalf("game architecture '%v' not supported\n", archi)
	}
	return nil
}
