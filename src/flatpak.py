import gi

gi.require_version('Flatpak', '1.0')

from gi.repository import GLib, Flatpak
from os import path

installation = Flatpak.get_system_installations()[0]
arch = Flatpak.get_default_arch()
remotes = installation.list_remotes()


def sync_remotes():
    """Sync all system remotes"""
    for remote in remotes:
        try:
            installation.update_remote_sync(remote.get_name(), None)
        except GLib.Error as err:
            print(err)


def update_appstream(remote):
    """Updates the local copy of appstream for remote"""
    print("Updating appstream for " + remote)
    try:
        installation.update_appstream_full_sync(remote.get_name(), arch, None, None, None)
    except GLib.Error as err:
        print(err)
    else:
        print("Updated appstream for " + remote)


def get_updates() -> list[Flatpak.InstalledRef]:
    """Returns a list of available updates"""
    return installation.list_installed_refs_for_update(None)


def installed_apps() -> list[Flatpak.InstalledRef]:
    """Returns a list of installed applications"""
    return installation.list_installed_refs_by_kind(Flatpak.RefKind.APP, None)


def num_of_installed_apps():
    """Returns the number of installed applications"""
    return len(installed_apps())


def num_of_updatable_apps():
    """Returns the number of updatable applications"""
    return len(get_updates())


def install_app(file):
    """Installs an application from a ref file"""
    filename = path.basename(file)
    print("Installing " + filename)
    with open(file, 'rb') as f:
        contents = f.read()
        contents = GLib.Bytes.new(contents)

        try:
            transaction = Flatpak.Transaction.new_for_installation(installation, None)
            transaction.add_install_flatpakref(contents)
            transaction.run()
        except GLib.Error as err:
            print(err)
        else:
            print("Installed " + filename)


def update_app(ref):
    """Updates an application"""
    print("Updating " + ref.get_appdata_name())
    try:
        transaction = Flatpak.Transaction.new_for_installation(installation, None)
        transaction.add_update(ref.format_ref(), None, None)
        transaction.run()
    except GLib.Error as err:
        print(err)
    else:
        print("Updated " + ref.get_appdata_name())


def update_all_apps():
    """Updates all installed applications"""
    for app in get_updates():
        update_app(app)


def uninstall_app(ref):
    """Uninstalls an application"""
    print("Uninstalling " + ref.get_appdata_name())
    try:
        transaction = Flatpak.Transaction.new_for_installation(installation, None)
        transaction.add_uninstall(ref.format_ref())
        transaction.run()
    except GLib.Error as err:
        print(err)
    else:
        print("Uninstalled " + ref.get_appdata_name())
