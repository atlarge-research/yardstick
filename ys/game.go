package main

import (
	"log"
	"path/filepath"

	"github.com/jdonkervliet/hocon"
)

type Game struct {
	Program
	Host string
	Port int
}

func (game *Game) Deploy(node *Node) error {
	// TODO support serverless game, uses an HTTP endpoint, port 443
	game.Host = node.ipAddress
	game.Port = 25565 // TODO prevent hard coding MC port
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
			rel := filepath.Join(basePath, local)
			resourcesPaths[i] = LocalRemotePathFromStrings(rel, remote)
		}
		return &Game{
			Program: &Jar{
				name:         "mve",
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
