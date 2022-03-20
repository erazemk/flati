package flatpak

import "fmt"

// Package holds all the info Flatpak reports about its packages
type Package struct {
	name         string
	description  string
	id           string
	version      string
	branch       string
	arch         string
	origin       string
	installation string
	ref          string
	size         string
	options      string
}

// Param returns the value of the chosen parameter of Package p
func (p *Package) Param(param string) (string, error) {
	switch param {
	case "name":
		return p.name, nil
	case "description":
		return p.description, nil
	case "id":
		return p.id, nil
	case "version":
		return p.version, nil
	case "branch":
		return p.branch, nil
	case "arch":
		return p.arch, nil
	case "origin":
		return p.origin, nil
	case "installation":
		return p.installation, nil
	case "ref":
		return p.ref, nil
	case "size":
		return p.size, nil
	case "options":
		return p.options, nil
	}

	return "", fmt.Errorf("not a valid parameter: %s", param)
}

// Name returns the package's name
func (p *Package) Name() string {
	return p.name
}

// Description returns the package's description
func (p *Package) Description() string {
	return p.description
}

// ID returns the package's ID (reverse domain notation)
func (p *Package) ID() string {
	return p.id
}

// Version returns the package's version
func (p *Package) Version() string {
	return p.version
}

// Branch returns the package's branch (main, beta, ...)
func (p *Package) Branch() string {
	return p.branch
}

// Arch returns the package's architecture
func (p *Package) Arch() string {
	return p.arch
}

// Origin returns the package's repository name
func (p *Package) Origin() string {
	return p.origin
}

// Installation returns the package's installation mode (user, system, oci, ...)
func (p *Package) Installation() string {
	return p.installation
}

// Ref returns the package's ref (id/arch/branch)
func (p *Package) Ref() string {
	return p.ref
}

// Size returns the package's size on disk
func (p *Package) Size() string {
	return p.size
}

// Options returns the package's options
func (p *Package) Options() string {
	return p.options
}
