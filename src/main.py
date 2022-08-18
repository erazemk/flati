import logging
import gi
import flatpak
import argparse

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

parser = argparse.ArgumentParser(description="Flati")
parser.add_argument("--debug", action="store_true", default=False, help="Enable debug output")
logging.basicConfig(level=logging.DEBUG if parser.parse_args().debug else logging.WARNING)

log = logging.getLogger('main')


# TODO: Add Explore tab, parse appstream for each app and show info
# TODO: Fix native file chooser not closing on file selection
# TODO: Try beautifulsoup for parsing appstream


class Flati:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("window.ui")
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("window")
        self.window_stack = self.builder.get_object("window_stack")
        self.app_list_button = self.builder.get_object("app_list_button")

        self.window_stack.connect("notify::visible-child", self.on_stack_visible_child_switch)
        self.fill_list_box()

    def fill_list_box(self):
        """Fills the list box with the applications"""
        window_name = self.window_stack.get_visible_child_name()
        no_apps_label_markup = ""
        listbox = None
        app_list = []

        # Fill application list based on visible window
        match window_name:
            case "installed-apps":
                app_list = flatpak.get_installed_apps()
                listbox = self.builder.get_object("app_list_box")
                no_apps_label_markup = "<span size='large' weight='bold'>No installed applications</span>"
            case "updatable-apps":
                app_list = flatpak.get_updatable_apps()
                listbox = self.builder.get_object("updates_list_box")
                no_apps_label_markup = "<span size='large' weight='bold'>All applications are up-to-date</span>"
            case _:
                log.error("Unknown window name: " + window_name)

        # Remove previous listed applications
        [listbox.remove(child) for child in listbox.get_children()]

        # Debug: Print list of applications
        log.debug("Apps for '{}': {}".format(window_name, [app.get_name() for app in app_list]))

        if len(app_list) != 0:
            log.debug("'{}' has {} apps".format(window_name, len(app_list)))

            for app in app_list:
                row_builder = Gtk.Builder()
                row_builder.add_from_file("applist.ui")
                row_builder.connect_signals(self)
                row = row_builder.get_object("app_row")

                app_icon = row_builder.get_object("app_icon")
                app_icon.set_from_file(flatpak.get_app_icon(app))

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

                if window_name == "updatable-apps":
                    app_button.set_property("label", "Update")

                listbox.add(row)
        else:
            # Debug: Display a message if no applications are installed/updatable
            log.debug("No apps for " + window_name)
            no_apps_label = Gtk.Label()
            no_apps_label.set_markup(no_apps_label_markup)

            list_box_row = Gtk.ListBoxRow()
            list_box_row.add(no_apps_label)
            list_box_row.set_property("expand", True)

            listbox.add(list_box_row)

        self.window.show_all()

    def on_stack_visible_child_switch(self, widget, param):
        """Updates app list button label based on visible window"""
        window_name = self.window_stack.get_visible_child_name()

        match window_name:
            case "installed-apps":
                self.app_list_button.set_label("Install new")
            case "updatable-apps":
                self.app_list_button.set_label("Update all")
            case _:
                log.error("Unknown window name: " + window_name)

        self.fill_list_box()

    def on_app_list_button_clicked(self, widget):
        """Either installs a new application from .flatpakref or updates all installed applications"""
        window_name = self.window_stack.get_visible_child_name()

        match window_name:
            case "installed-apps":
                # Install new application
                dialog = self.builder.get_object("file_chooser")
                response = dialog.run()

                if response == Gtk.ResponseType.ACCEPT:
                    file = dialog.get_filename()
                    dialog.hide()
                    flatpak.install_app(file)
                    self.fill_list_box()
                else:
                    log.debug("No file selected")
            case "updatable-apps":
                # Update all applications
                flatpak.update_all_apps()
            case _:
                log.error("Unknown window name: " + window_name)

    def on_app_button_clicked(self, obj, ref):
        """Either uninstalls an application or updates it"""
        window_name = self.window_stack.get_visible_child_name()

        match window_name:
            case "installed-apps":
                flatpak.uninstall_app(ref)
                self.fill_list_box()
            case "updatable-apps":
                flatpak.update_app(ref)
                self.fill_list_box()
            case _:
                log.error("Unknown window name: " + window_name)

    def on_close_dialog(self, widget, event):
        return self.builder.get_object("file_chooser_dialog").hide_on_delete()


Flati()
Gtk.main()
flatpak.cleanup()
