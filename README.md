# Flati

A GTK4 app store for [Flatpak](https://flatpak.org/), written in Go.
Uses [erazemk/go-flatpak](https://github.com/erazemk/go-flatpak) to interface with Flatpak.

## Building

1. Install dependencies
    * Fedora: `sudo dnf install -y flatpak gtk4-devel gobject-introspection-devel`
    * Ubuntu: `sudo apt install -y flatpak libflatpak-dev libgtk-4-dev gobject-introspection`
2. (Optional) Pre-compile gotk4: `go get -v github.com/diamondburned/gotk4/pkg/gtk/v4`
3. Build the project: `go build -v github.com/erazemk/flati`

## License

This project is licensed under the [GNU GPLv3](LICENSE) license.
