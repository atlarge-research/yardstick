package main

import (
	"path/filepath"
	"strconv"

	"github.com/jdonkervliet/hocon"
)

func PlayerEmulationFromConfig(host string, port int, configPath string) Program {
	config, err := hocon.ParseResource(configPath)
	if err != nil {
		panic(err)
	}
	basePath := config.GetString("benchmark.directories.input")
	jarPath := filepath.Join(basePath, config.GetString("benchmark.player-emulation.path"))
	return &Jar{
		name:    "player-emulation",
		JarPath: LocalRemotePathFromStrings(jarPath, ""),
		// FIXME this config cannot be copied, but must be written to disk bc it can be the merge of multiple configs!
		JarArguments: []string{"--host", host, "--port", strconv.Itoa(port)},
		JVMArgs:      config.GetStringSlice("benchmark.player-emulation.jvm.options"),
		Resources:    []LocalRemotePath{LocalRemotePathFromStrings(configPath, "")},
	}
}
