import flatpak
import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk


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
        if flatpak.number_of_installed_applications() == 0:
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
        for app in flatpak.installed_applications():
            row_builder = Gtk.Builder()
            row_builder.add_from_file("applist.ui")
            row_builder.connect_signals(self)

            row = row_builder.get_object("app_row")

            # app_icon = self.builder.get_object("app_icon")

            app_name = row_builder.get_object("app_name")
            app_name.set_property("label", app.get_appdata_name())

            app_summary = row_builder.get_object("app_summary")
            app_summary.set_property("label", app.get_appdata_summary())

            app_version = row_builder.get_object("app_version")
            app_version.set_property("label", app.get_appdata_version())

            app_size = row_builder.get_object("app_size")
            app_size.set_property("label", str(round(app.get_installed_size() / 1000000.0, 1)) + " MB")

            uninstall_button = row_builder.get_object("uninstall_button")
            uninstall_button.connect("clicked", self.on_uninstall_button_clicked, app)

            listbox.add(row)

    def on_install_button_clicked(self, widget):
        dialog = self.builder.get_object("file_chooser")
        response = dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            path = dialog.get_filename()
            dialog.hide()
            flatpak.install(path)

            if flatpak.number_of_installed_applications() == 0:
                # Replace original window with list of applications
                self.window_stack.set_visible_child(self.list_window)
                self.fill_list_box()
            else:
                # Update list of applications
                self.fill_list_box()
        else:
            print("No file selected")

    def on_uninstall_button_clicked(self, obj, ref):
        flatpak.uninstall(ref)

        if flatpak.number_of_installed_applications() == 0:
            # Replace original window with empty window
            self.window_stack.set_visible_child(self.empty_window)
        else:
            # Update list of applications
            self.window_stack.set_visible_child(self.list_window)
            self.fill_list_box()

        self.window.show_all()

    def on_close_dialog(self, widget, event):
        return self.builder.get_object("file_chooser_dialog").hide_on_delete()


Flati()
Gtk.main()
