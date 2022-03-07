package main

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strconv"

	"github.com/gurkankaymak/hocon"
)

func PlayerEmulationFromConfig(address, configFilePath string, num int) (Program, error) {
	config, err := hocon.ParseResource(configFilePath)
	if err != nil {
		return nil, err
	}
	basePath := config.GetString("yardstick.directories.input")
	jarPath := filepath.Join(basePath, config.GetString("yardstick.player-emulation.path"))
	if _, err := os.Stat(jarPath); errors.Is(err, os.ErrNotExist) {
		return nil, fmt.Errorf("player emulation jar does not exist: %w", err)
	}
	lrJarPath := LocalRemotePathFromStrings(jarPath, "")
	jvmArgs := []string{"-Dconfig.file=application.conf"}
	lrConfigPath := LocalRemotePathFromStrings(configFilePath, "application.conf")
	if _, err := os.Stat(lrConfigPath.LocalPath); errors.Is(err, os.ErrNotExist) {
		return nil, fmt.Errorf("player emulation config does not exist: %w", err)
	}
	return &Jar{
		name:         "playerEmulation",
		JarPath:      lrJarPath,
		JarArguments: []string{"--address", address, "--nodeID", strconv.Itoa(num)},
		JVMArgs:      append(jvmArgs, config.GetStringSlice("yardstick.player-emulation.jvm.options")...),
		Resources:    []LocalRemotePath{lrConfigPath},
	}, nil
}
