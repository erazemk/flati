package window

import (
	_ "embed"
	"os"
	"strconv"

	"github.com/diamondburned/gotk4/pkg/gtk/v4"
	_ "github.com/erazemk/flati/internal/flatpak"
)

//go:embed flati.ui
var uiFileXML string

func Start() {
	app := gtk.NewApplication("eu.erazem.flati", 0)
	app.ConnectActivate(func() { activate(app) })

	if code := app.Run(os.Args); code > 0 {
		os.Exit(code)
	}
}

func activate(app *gtk.Application) {
	counter := 0
	builder := gtk.NewBuilderFromString(uiFileXML, len(uiFileXML))
	window := builder.GetObject("Window").Cast().(*gtk.Window)
	button := builder.GetObject("Button").Cast().(*gtk.Button)

	button.Connect("clicked", func() {
		counter++
		button.SetLabel(strconv.Itoa(counter))
	})

	app.AddWindow(window)
	window.SetChild(button)
	window.Show()
}
