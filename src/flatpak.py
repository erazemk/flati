import gi

gi.require_version('Flatpak', '1.0')

from gi.repository import GLib, Flatpak
from os import path

installation = Flatpak.get_system_installations()[0]
remotes = installation.list_remotes()


def sync_remotes():
    """Sync all system remotes"""
    for remote in remotes:
        try:
            installation.update_remote_sync(remote.get_name(), None)
        except GLib.Error as err:
            print(err)


def installed_applications() -> list[Flatpak.InstalledRef]:
    """Returns a list of installed applications"""
    return installation.list_installed_refs_by_kind(Flatpak.RefKind.APP, None)


def number_of_installed_applications():
    """Returns the number of installed applications"""
    return len(installed_applications())


def install(file):
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


def uninstall(ref):
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
