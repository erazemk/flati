import argparse
import logging
import gi
import flatpak

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib

parser = argparse.ArgumentParser(description="Flati")
parser.add_argument("--debug", action="store_true", default=False, help="Enable debug output")

logging.basicConfig(level=logging.DEBUG if parser.parse_args().debug else logging.WARNING)
log = logging.getLogger('Flati.main')


# TODO: Get app info in a separate thread to avoid locking up UI


class Flati:
    remote_apps_list_updated = False

    def __init__(self):
        """Initializes GTK elements"""
        self.builder = Gtk.Builder()
        self.builder.add_from_file("window.ui")
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("window")
        self.window.connect("destroy", Gtk.main_quit)

        self.window_stack = self.builder.get_object("window_stack")
        self.window_stack.set_visible_child_name("installed-apps")
        self.window_stack.connect("notify::visible-child", self.on_stack_visible_child_update)

        self.app_list_button = self.builder.get_object("app_list_button")
        GLib.idle_add(self.fill_app_list_box)

    def fill_app_list_box(self):
        """Adds list of applications to currently visible tab of window stack"""
        tab_name = self.window_stack.get_visible_child_name()
        listbox = None
        app_list = []
        no_apps_text = ""

        # Fill application list based on visible tab
        match tab_name:
            case "installed-apps":
                app_list = flatpak.get_installed_apps_info()
                listbox = self.builder.get_object("app_list_box")
                no_apps_text = "No installed applications"
            case "updatable-apps":
                app_list = flatpak.get_updatable_apps_info()
                listbox = self.builder.get_object("updates_list_box")
                no_apps_text = "All applications are up-to-date"
            case "explore-apps":
                app_list = flatpak.get_remote_apps_info()
                listbox = self.builder.get_object("explore_list_box")
                no_apps_text = "Could not find any remote apps"
            case _:
                log.error("Unknown window name: " + tab_name)

        # Remove previous listed applications
        [listbox.remove(child) for child in listbox.get_children()]

        # If no apps found show an appropriate message/label
        if len(app_list) == 0:
            log.debug("No apps for '{}'".format(tab_name))
            no_apps_label = Gtk.Label()
            no_apps_label_markup = "<span size='large' weight='bold'>{}</span>".format(no_apps_text)
            no_apps_label.set_markup(no_apps_label_markup)

            list_box_row = Gtk.ListBoxRow()
            list_box_row.add(no_apps_label)
            list_box_row.set_property("expand", True)

            listbox.add(list_box_row)
            self.window.show_all()
            return

        log.debug("'{}' has {} apps".format(tab_name, len(app_list)))
        for app_info in app_list:
            row_builder = Gtk.Builder()
            row_builder.add_from_file("applist.ui")
            row_builder.connect_signals(self)
            row = row_builder.get_object("app_row")

            app_icon = row_builder.get_object("app_icon")
            app_icon.set_from_file(app_info["icon"])

            app_name = row_builder.get_object("app_name")
            app_name.set_property("label", app_info["name"])

            app_summary = row_builder.get_object("app_summary")
            app_summary.set_property("label", app_info["summary"])

            app_version = row_builder.get_object("app_version")
            app_version.set_property("label", app_info["version"])

            app_size = row_builder.get_object("app_size")
            app_size.set_property("label", app_info["size-str"])

            app_button = row_builder.get_object("app_button")
            app_button.connect("clicked", self.on_app_button_clicked, app_info)

            match tab_name:
                case "installed-apps":
                    app_button.set_property("label", "Uninstall")
                case "updatable-apps":
                    app_button.set_property("label", "Update")
                case "explore-apps":
                    app_button.set_property("label", "Install")

                    for installed_app in flatpak.get_installed_apps_info():
                        if installed_app["id"] == app_info["id"]:
                            app_button.set_sensitive(False)
                            app_button.set_property("label", "Installed")
                case _:
                    log.error("Unknown window name: " + tab_name)

            listbox.add(row)

        if tab_name == "explore-apps":
            self.remote_apps_list_updated = True

        self.window.show_all()

    def on_stack_visible_child_update(self, widget, param):
        """Updates app list button label based on visible tab of window stack"""
        window_name = self.window_stack.get_visible_child_name()

        match window_name:
            case "installed-apps":
                self.app_list_button.set_label("Install new")
            case "updatable-apps":
                self.app_list_button.set_label("Update all")
            case "explore-apps":
                self.app_list_button.set_label("Refresh")
            case _:
                log.error("Unknown window name: " + window_name)

        if window_name in ("installed-apps", "updatable-apps") or not self.remote_apps_list_updated:
            GLib.idle_add(self.fill_app_list_box)

    def on_app_list_button_clicked(self, widget):
        """Executes an action based on visible tab of window stack"""
        window_name = self.window_stack.get_visible_child_name()
        match window_name:
            case "installed-apps":  # Install new application from .flatpakref file
                dialog = self.builder.get_object("file_chooser")
                response = dialog.run()

                if response == Gtk.ResponseType.ACCEPT:
                    file = dialog.get_filename()
                    dialog.hide()
                    flatpak.install_local_ref(file)
                else:
                    log.debug("No file selected")
            case "updatable-apps":  # Update all installed refs
                flatpak.update_all_refs()
            case "explore-apps":  # Update appstream data for all remotes
                self.remote_apps_list_updated = False
                flatpak.update_remote_info()
                flatpak.parse_all_remote_xmls()
            case _:
                log.error("Unknown window name: " + window_name)

        GLib.idle_add(self.fill_app_list_box)

    def on_app_button_clicked(self, obj, app_info):
        """Executes an action based on clicked app id and visible tab of window stack"""
        window_name = self.window_stack.get_visible_child_name()
        match window_name:
            case "installed-apps":
                flatpak.uninstall_ref(app_info["ref"])
            case "updatable-apps":
                flatpak.update_ref(app_info["ref"])
            case "explore-apps":
                flatpak.install_remote_ref(app_info["ref"].format_ref(), app_info["remote"])
                obj.set_sensitive(False)
                obj.set_property("label", "Installed")
            case _:
                log.error("Unknown window name: " + window_name)

        # Update app list if necessary
        if window_name in ("installed-apps", "updatable-apps"):
            GLib.idle_add(self.fill_app_list_box)

    def on_close_dialog(self, widget, event):
        return self.builder.get_object("file_chooser_dialog").hide_on_delete()


flatpak.parse_all_remote_xmls()
Flati()
Gtk.main()
