import gi

gi.require_version("Gtk", "3.0")
gi.require_version('Flatpak', '1.0')

from gi.repository import Gtk, GLib, Flatpak

installation = Flatpak.get_system_installations()[0]


def get_installed_applications() -> list[Flatpak.InstalledRef]:
    return installation.list_installed_refs_by_kind(Flatpak.RefKind.APP, None)


class Flati:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("flati.ui")
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("flati_window")
        self.window.show_all()

    def on_open_dialog(self, widget):
        dialog = self.builder.get_object("file_chooser_dialog")
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            path = dialog.get_filename()
            dialog.close()
            self.install_flatpak(path)
        else:
            dialog.close()

    def on_close_dialog(self, widget, event):
        return self.builder.get_object("file_chooser_dialog").hide_on_delete()

    def install_flatpak(self, path):
        with open(path, 'rb') as f:
            contents = f.read()
            contents = GLib.Bytes.new(contents)

            try:
                transaction = Flatpak.Transaction.new_for_installation(installation, None)
                transaction.add_install_flatpakref(contents)
                transaction.run()
            except GLib.Error as err:
                if err.matches(GLib.quark_from_string("flatpak-error-quark"), Flatpak.Error.ALREADY_INSTALLED):
                    self.builder.get_object("install_label").set_property("label", "Already installed")
                else:
                    self.builder.get_object("install_label").set_property("label", "Unknown error occured")
                    print(err)
            else:
                self.builder.get_object("install_label").set_property("label", "Application installed")

    def uninstall_flatpak(self, path):
        pass


Flati()
Gtk.main()
