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
	jvmArgs := []string{"-Dconfig.file=application.conf"}
	return &Jar{
		name:         "playerEmulation",
		JarPath:      LocalRemotePathFromStrings(jarPath, ""),
		JarArguments: []string{"--host", host, "--port", strconv.Itoa(port)},
		JVMArgs:      append(jvmArgs, config.GetStringSlice("benchmark.player-emulation.jvm.options")...),
		// FIXME this config cannot be copied, but must be written to disk bc it can be the merge of multiple configs!
		Resources: []LocalRemotePath{LocalRemotePathFromStrings(configPath, "")},
	}
}
