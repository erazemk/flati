# Flati

A GTK4 app store for [Flatpak](https://flatpak.org/), written in Go.

## Building

```shell
# Install dependencies
sudo dnf install -y flatpak gtk4-devel gobject-introspection-devel

# (Optional) Pre-compile gotk4
go get -v github.com/diamondburned/gotk4/pkg/gtk/v4

# Build the project
go build github.com/erazemk/flati
```

## License

This project is licensed under the [GNU GPLv3](LICENSE) license.
