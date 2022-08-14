import logging
import gi

gi.require_version('Flatpak', '1.0')

from gi.repository import GLib, Flatpak
from os import path

installation = Flatpak.get_system_installations()[0]
arch = Flatpak.get_default_arch()
remotes = installation.list_remotes()

log = logging.getLogger('flatpak')


def sync_remotes():
    """Sync all system remotes"""
    log.debug("Syncing remotes")

    for remote in remotes:
        try:
            installation.update_remote_sync(remote.get_name(), None)
        except GLib.Error as err:
            log.error(err)


def get_remote_apps() -> [Flatpak.RemoteRef]:
    """Returns a list of remote applications"""
    log.debug("Getting remote applications")
    remote_apps = []

    for remote in remotes:
        if remote.get_disabled() is False:
            remote_apps.extend(installation.list_remote_refs_sync(remote.get_name(), None))
            installation.update_appstream_sync(remote.get_name(), arch, None, None)

    return remote_apps


def update_appstream(remote):
    """Updates the local copy of appstream for remote"""
    log.debug("Updating appstream for " + remote)

    try:
        installation.update_appstream_full_sync(remote.get_name(), arch, None, None, None)
    except GLib.Error as err:
        log.error(err)
    else:
        log.debug("Updated appstream for " + remote)


def get_updates() -> [Flatpak.InstalledRef]:
    """Returns a list of available updates"""
    log.debug("Getting updates")
    return installation.list_installed_refs_for_update(None)


def get_installed_apps() -> [Flatpak.InstalledRef]:
    """Returns a list of installed applications"""
    log.debug("Getting installed applications")
    return installation.list_installed_refs_by_kind(Flatpak.RefKind.APP, None)


def get_num_of_installed_apps() -> int:
    """Returns the number of installed applications"""
    log.debug("Getting number of installed applications")
    return len(get_installed_apps())


def get_num_of_updatable_apps() -> int:
    """Returns the number of updatable applications"""
    log.debug("Getting number of updatable applications")
    return len(get_updates())


def install_app(file):
    """Installs an application from a ref file"""
    filename = path.basename(file)
    log.debug("Installing " + filename)

    with open(file, 'rb') as f:
        contents = f.read()
        contents = GLib.Bytes.new(contents)

        try:
            transaction = Flatpak.Transaction.new_for_installation(installation, None)
            transaction.add_install_flatpakref(contents)
            transaction.run()
        except GLib.Error as err:
            log.error(err)
        else:
            log.debug("Installed " + filename)


def update_app(ref):
    """Updates an application"""
    log.debug("Updating " + ref.get_appdata_name())

    try:
        transaction = Flatpak.Transaction.new_for_installation(installation, None)
        transaction.add_update(ref.format_ref(), None, None)
        transaction.run()
    except GLib.Error as err:
        log.error(err)
    else:
        log.debug("Updated " + ref.get_appdata_name())


def update_all_apps():
    """Updates all installed applications"""
    log.debug("Updating all applications")
    [update_app(app) for app in get_updates()]


def uninstall_app(ref):
    """Uninstalls an application"""
    log.debug("Uninstalling " + ref.get_appdata_name())

    try:
        transaction = Flatpak.Transaction.new_for_installation(installation, None)
        transaction.add_uninstall(ref.format_ref())
        transaction.run()
    except GLib.Error as err:
        log.error(err)
    else:
        log.debug("Uninstalled " + ref.get_appdata_name())
