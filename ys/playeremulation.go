package main

import (
	"net/url"
	"path/filepath"

	"github.com/jdonkervliet/hocon"
)

func PlayerEmulationFromConfig(game *url.URL, configPath string) Program {
	config, err := hocon.ParseResource(configPath)
	if err != nil {
		panic(err)
	}
	basePath := config.GetString("benchmark.directories.input")
	jarPath, err := filepath.Rel(basePath, config.GetString("path"))
	if err != nil {
		panic(err)
	}
	return &Jar{
		JarPath: LocalRemotePathFromStrings(jarPath, ""),
		// FIXME this config cannot be copied, but must be written to disk bc it can be the merge of multiple configs!
		JarArguments: []string{"--gameURL", game.String()},
		JVMArgs:      config.GetStringSlice("benchmark.player-emulation.jvm.options"),
		Resources:    []LocalRemotePath{LocalRemotePathFromStrings(configPath, "")},
	}
}
