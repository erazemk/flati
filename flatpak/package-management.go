package flatpak

import (
	"fmt"
	"os/exec"
)

// Install installs the requested package
func Install(p Package) error {
	cmd := exec.Command("flatpak", "install", "-y", p.id)

	// TODO: Default to using Flathub (get remote info from 'origin' column)

	if debug {
		fmt.Printf("Installing package '%s' (%s)\n", p.name, p.id)
	}

	err := cmd.Run()
	if err != nil {
		return err
	}

	return nil
}

// Uninstall uninstalls the requested package
func Uninstall(p Package, deleteData bool) error {
	var cmd *exec.Cmd

	if deleteData {
		cmd = exec.Command("flatpak", "uninstall", "-y", "--delete-data", p.id)
	} else {
		cmd = exec.Command("flatpak", "uninstall", "-y", p.id)
	}

	if debug {
		fmt.Printf("Uninstalling package '%s' (%s)\n", p.name, p.id)
	}

	err := cmd.Run()
	if err != nil {
		return err
	}

	return nil
}
