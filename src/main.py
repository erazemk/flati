import gi

gi.require_version("Gtk", "3.0")
gi.require_version('Flatpak', '1.0')

from gi.repository import Gtk, GLib, Flatpak

installation = Flatpak.get_system_installations()[0]


def get_installed_applications() -> list[Flatpak.InstalledRef]:
    return installation.list_installed_refs_by_kind(Flatpak.RefKind.APP, None)


remotes = installation.list_remotes()
for remote in remotes:

    try:
        installation.update_remote_sync(remote.get_name(), None)
    except GLib.Error as err:
        print(err)


class Flati:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("window.ui")
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("window")
        self.window_stack = self.builder.get_object("window_stack")
        self.empty_window = self.builder.get_object("empty_window")
        self.list_window = self.builder.get_object("list_window")

        # Either open new installation window or a list of installed applications
        if get_installed_applications() is []:
            self.window_stack.set_visible_child(self.empty_window)
        else:
            self.window_stack.set_visible_child(self.list_window)
            self.fill_list_box()

        self.window.show_all()

    def fill_list_box(self):
        listbox = self.builder.get_object("app_list_box")
        for child in listbox.get_children():
            listbox.remove(child)

        # Fill list with installed applications
        for flatpak in get_installed_applications():
            row_builder = Gtk.Builder()
            row_builder.add_from_file("window.ui")
            row_builder.connect_signals(self)

            row = row_builder.get_object("box_row")

            # app_icon = self.builder.get_object("app_icon")

            app_name = row_builder.get_object("app_name")
            app_name.set_property("label", flatpak.get_appdata_name())

            app_summary = row_builder.get_object("app_summary")
            app_summary.set_property("label", flatpak.get_appdata_summary())

            app_version = row_builder.get_object("app_version")
            app_version.set_property("label", flatpak.get_appdata_version())

            app_size = row_builder.get_object("app_size")
            app_size.set_property("label", str(round(flatpak.get_installed_size() / 1000000.0, 1)) + " MB")

            uninstall_button = row_builder.get_object("uninstall_button")
            uninstall_button.connect("clicked", self.uninstall_flatpak, flatpak)

            listbox.add(row)

    def on_open_dialog(self, widget):
        dialog = self.builder.get_object("file_chooser")
        response = dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            path = dialog.get_filename()
            dialog.hide()
            self.install_flatpak(path)
        else:
            print("No file selected")

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
                print("Installed " + path)
                if first_install:
                    # Replace original window with list of applications
                    self.window_stack.set_visible_child(self.list_window)
                    self.fill_list_box()
                else:
                    # Update list of applications
                    self.fill_list_box()

    def uninstall_flatpak(self, obj, ref):
        print("Pressed uninstall button for " + ref.get_appdata_name())
        try:
            transaction = Flatpak.Transaction.new_for_installation(installation, None)
            transaction.add_uninstall(ref.format_ref())
            transaction.run()
        except GLib.Error as err:
            print(err)
        else:
            print("Uninstalled " + ref.get_appdata_name())
            first_install = True if get_installed_applications() is [] else False

            if first_install:
                # Replace original window with list of applications
                self.window_stack.set_visible_child(self.empty_window)
            else:
                # Update list of applications
                self.window_stack.set_visible_child(self.list_window)
                self.fill_list_box()

            self.window.show_all()


Flati()
Gtk.main()
