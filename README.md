# Flati

A GTK app store for [Flatpak](https://flatpak.org/), written in Go.

## Building

1. Install Flatpak and GTK4 development libraries:
`sudo dnf install -y flatpak gtk4-devel gobject-introspection-devel`
2. Download and compile Go's GTK4 bindings (gotk4):
`go get -v github.com/diamondburned/gotk4/pkg/gtk/v4` (this will take a while)
3. Build the project: `go build github.com/erazemk/flati`

## Features

- [Flatpak features to (not) be implemented](flatpak/README.md)

## License

This project is licensed under the [GNU GPLv3](LICENSE) license.