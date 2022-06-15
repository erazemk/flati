package main

import (
	"os"

	"github.com/erazemk/flati/internal/flatpak"
	"github.com/erazemk/flati/internal/window"
	"github.com/pborman/getopt/v2"
)

func main() {
	// Parse command flags
	debugFlag := getopt.BoolLong("debug", 'd', "Print debug info")
	helpFlag := getopt.BoolLong("help", 'h', "Print this text")
	getopt.Parse()

	if *helpFlag {
		getopt.Usage()
		os.Exit(0)
	}

	flatpak.SetDebug(*debugFlag)
	window.Start()
}
