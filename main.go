package main

import (
	"github.com/erazemk/flati/ui"
	"os"

	"github.com/erazemk/flati/flatpak"
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

	// Enable debug output if requested
	flatpak.SetDebug(*debugFlag)

	//fmt.Println(flatpak.Search("faaaaaaa"))

	// Start a GTK window
	ui.Start()
}
