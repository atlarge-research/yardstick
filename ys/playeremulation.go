package main

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"

	"github.com/jdonkervliet/hocon"
)

func PlayerEmulationFromConfig(address, configFilePath string) (Program, error) {
	config, err := hocon.ParseResource(configFilePath)
	if err != nil {
		return nil, err
	}
	basePath := config.GetString("benchmark.directories.input")
	jarPath := filepath.Join(basePath, config.GetString("benchmark.player-emulation.path"))
	if _, err := os.Stat(jarPath); errors.Is(err, os.ErrNotExist) {
		return nil, fmt.Errorf("player emulation jar does not exist: %w", err)
	}
	lrJarPath := LocalRemotePathFromStrings(jarPath, "")
	jvmArgs := []string{"-Dconfig.file=application.conf"}
	lrConfigPath := LocalRemotePathFromStrings(configFilePath, "")
	if _, err := os.Stat(lrConfigPath.LocalPath); errors.Is(err, os.ErrNotExist) {
		return nil, fmt.Errorf("player emulation config does not exist: %w", err)
	}
	return &Jar{
		name:         "playerEmulation",
		JarPath:      lrJarPath,
		JarArguments: []string{"--address", address},
		JVMArgs:      append(jvmArgs, config.GetStringSlice("benchmark.player-emulation.jvm.options")...),
		// FIXME this config cannot be copied, but must be written to disk bc it can be the merge of multiple configs!
		Resources: []LocalRemotePath{lrConfigPath},
	}, nil
}
