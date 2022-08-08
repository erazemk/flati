import gi

gi.require_version("Gtk", "3.0")
gi.require_version('Flatpak', '1.0')

from gi.repository import Gtk, GLib, Flatpak

installation = Flatpak.get_system_installations()[0]


def get_installed_applications() -> list[Flatpak.InstalledRef]:
    return installation.list_installed_refs_by_kind(Flatpak.RefKind.APP, None)


remotes = installation.list_remotes()
for remote in remotes:
    print(remote.get_name())

    try:
        installation.update_remote_sync(remote.get_name(), None)
    except GLib.Error as err:
        print(err)
    else:
        print("Updated remote {}".format(remote.get_name()))


class Flati:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("flati.ui")
        self.builder.connect_signals(self)

        # Either open new installation window or a list of installed applications
        if get_installed_applications() is []:
            self.window = self.builder.get_object("initial_window")
        else:
            self.window = self.builder.get_object("main_window")
            self.fill_list_box()

        self.window.show_all()

    def fill_list_box(self):
        listbox = self.builder.get_object("app_list_box")

        # Fill list with installed applications
        for flatpak in get_installed_applications():
            builder2 = Gtk.Builder()
            builder2.add_from_file("flati.ui")
            row = builder2.get_object("box_row")

            app_name = builder2.get_object("app_name")
            app_name.set_property("label", flatpak.get_appdata_name())

            app_summary = builder2.get_object("app_summary")
            app_summary.set_property("label", flatpak.get_appdata_summary())

            app_version = builder2.get_object("app_version")
            app_version.set_property("label", flatpak.get_appdata_version())

            app_size = builder2.get_object("app_size")
            app_size.set_property("label", str(round(flatpak.get_installed_size() / 1000000.0, 1)) + " MB")

            #button = builder2.get_object("uninstall_button")
            #button.connect("pressed", self.uninstall_flatpak(flatpak))

            listbox.add(row)

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
        first_install = True if get_installed_applications() is [] else False

        with open(path, 'rb') as f:
            contents = f.read()
            contents = GLib.Bytes.new(contents)

            try:
                transaction = Flatpak.Transaction.new_for_installation(installation, None)
                transaction.add_install_flatpakref(contents)
                transaction.run()
            except GLib.Error as err:
                print(err)
            else:
                if first_install:
                    # Replace original window with list of applications
                    self.window.close()
                    self.window = self.builder.get_object("main_window")
                    self.fill_list_box()
                    self.window.show_all()
                else:
                    # Update list of applications
                    self.fill_list_box()
                    self.window.show_all()

    def uninstall_flatpak(self, ref):
        print("Pressed uninstall button for " + ref.get_appdata_name())
        try:
            transaction = Flatpak.Transaction.new_for_installation(installation, None)
            transaction.add_uninstall(ref.format_ref())
            #transaction.run()
        except GLib.Error as err:
            print(err)
        else:
            first_install = True if get_installed_applications() is [] else False

            if first_install:
                # Replace original window with list of applications
                self.window.close()
                self.window = self.builder.get_object("main_window")
                self.fill_list_box()
                self.window.show_all()
            else:
                # Update list of applications
                self.fill_list_box()
                self.window.show_all()


Flati()
Gtk.main()
