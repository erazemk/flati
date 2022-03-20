package ui

import (
	_ "embed"
	"os"

	"github.com/diamondburned/gotk4/pkg/gtk/v4"
	"github.com/erazemk/flati/flatpak"
)

//go:embed flati.ui
var uiFileXML string

// Start launches a GTK window
func Start() {
	app := gtk.NewApplication("eu.erazem.flati", 0)
	app.ConnectActivate(func() { activate(app) })

	if code := app.Run(os.Args); code > 0 {
		os.Exit(code)
	}
}

func activate(app *gtk.Application) {
	counter := 0
	apps := flatpak.List("app")
	builder := gtk.NewBuilderFromString(uiFileXML, len(uiFileXML))

	window := builder.GetObject("Window").Cast().(*gtk.Window)
	button := builder.GetObject("Button").Cast().(*gtk.Button)

	button.Connect("clicked", func() {
		if counter < len(apps) {
			button.SetLabel(apps[counter].Name())
			counter++
		} else {
			counter = 0
		}
	})

	app.AddWindow(window)
	window.SetChild(button)
	window.Show()
}
