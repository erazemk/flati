all: build run

build:
	go build -v github.com/erazemk/flati

clean:
	rm flati

run:
	go run github.com/erazemk/flati

deps:
	sudo dnf install -y flatpak gtk4-devel gobject-introspection-devel
	go get -v github.com/diamondburned/gotk4/pkg/gtk/v4
	go get -v github.com/pborman/getopt/v2

.PHONY: all clean run
