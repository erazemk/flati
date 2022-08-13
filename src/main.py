import gi

import flatpak

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk


class Flati:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("window.ui")
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("window")
        self.window_stack = self.builder.get_object("window_stack")
        self.list_window = self.builder.get_object("list_window")
        self.app_list_button = self.builder.get_object("app_list_button")

        self.window_stack.connect("notify::visible-child", self.on_stack_visible_child_switch)

        if flatpak.num_of_installed_apps() == 0:
            # TODO: Add a label saying there are no installed applications
            pass
        else:
            self.fill_list_box()

        self.window.show_all()

    def fill_list_box(self):
        listbox = self.builder.get_object("app_list_box")
        for child in listbox.get_children():
            listbox.remove(child)

        window_name = self.window_stack.get_visible_child_name()

        app_list = []
        if window_name == "installed-apps":
            # Fill list with installed applications
            app_list = flatpak.installed_apps()
        elif window_name == "updatable-apps":
            # Fill list with updatable applications
            app_list = flatpak.get_updates()
        else:
            print("Unknown window name: " + window_name)

        for app in app_list:
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

            app_button = row_builder.get_object("app_button")
            app_button.connect("clicked", self.on_app_button_clicked, app)

            listbox.add(row)

    def on_stack_visible_child_switch(self, widget, param):
        """Updates app list button label based on the visible child of the stack"""
        window_name = self.window_stack.get_visible_child_name()

        if window_name == "installed-apps":
            self.app_list_button.set_label("Install new")
        elif window_name == "updatable-apps":
            self.app_list_button.set_label("Update all")
        else:
            print("Unknown window name: " + window_name)

        self.fill_list_box()

    def on_app_list_button_clicked(self, widget):
        """Either installs a new application from .flatpakref or updates all installed applications"""
        window_name = self.window_stack.get_visible_child_name()

        if window_name == "installed-apps":
            # Install new application
            dialog = self.builder.get_object("file_chooser")
            response = dialog.run()

            if response == Gtk.ResponseType.ACCEPT:
                file = dialog.get_filename()
                dialog.hide()
                flatpak.install_app(file)

                if flatpak.num_of_installed_apps() == 0:
                    # TODO: Add a label saying there are no installed applications
                    pass
                else:
                    self.fill_list_box()
            else:
                print("No file selected")
        elif window_name == "updatable-apps":
            # Update all applications
            flatpak.update_all_apps()
        else:
            print("Unknown window name: " + window_name)

    def on_app_button_clicked(self, obj, ref):
        """Either uninstalls an application or updates it"""
        window_name = self.window_stack.get_visible_child_name()

        if window_name == "installed-apps":
            flatpak.uninstall_app(ref)

            if flatpak.num_of_installed_apps() == 0:
                # TODO: Add a label saying there are no installed applications
                pass
            else:
                self.fill_list_box()
        elif window_name == "updatable-apps":
            flatpak.update_app(ref)

            if flatpak.num_of_updatable_apps() == 0:
                # TODO: Add a label saying there are no updatable applications
                pass
            else:
                self.fill_list_box()
        else:
            print("Unknown window name: " + window_name)

    def on_close_dialog(self, widget, event):
        return self.builder.get_object("file_chooser_dialog").hide_on_delete()


Flati()
Gtk.main()
