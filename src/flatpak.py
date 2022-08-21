import configparser
import gzip
import logging
import shutil
import tempfile
import threading

import gi
import requests

gi.require_version('Flatpak', '1.0')

from gi.repository import GLib, Flatpak
from os import path
from bs4 import BeautifulSoup

installation = Flatpak.get_system_installations()[0]
arch = Flatpak.get_default_arch()
session = requests.Session()
log = logging.getLogger('flatpak')
tempdir = tempfile.TemporaryDirectory()
config = configparser.ConfigParser()
appstream_xml = {}
xml_parsing_threads: {str, threading.Thread} = {}


def get_remotes() -> [Flatpak.Remote]:
    all_remotes: [Flatpak.Remote] = installation.list_remotes()

    remote_list = []
    for remote in all_remotes:
        remote_url = remote.get_url()
        if not remote_url.startswith("oci+") and not remote.get_disabled():
            remote_list.append(remote)

    log.info("Remotes: " + str(remote_list))
    return remote_list


remotes = get_remotes()


def sync_remotes():
    """Sync all system remotes"""
    log.debug("Syncing remotes")

    for remote in remotes:
        try:
            installation.update_remote_sync(remote.get_name(), None)
        except GLib.Error as err:
            log.error(err)


def parse_remote_xml(remote_name):
    """Parses appstream xml for a remote"""
    xml_path = installation.get_remote_by_name(remote_name).get_appstream_dir().get_path()
    xml_file = xml_path + "/active/appstream.xml.gz"

    if not path.exists(xml_file):
        xml_file = xml_path + "/appstream.xml.gz"

    if not path.exists(xml_file):
        log.error("XML file for {} not found!".format(remote_name))

    log.debug("Parsing XML for " + remote_name)

    if remote_name not in appstream_xml:
        with gzip.open(xml_file, 'rb') as archive:
            appstream_xml[remote_name] = BeautifulSoup(archive.read(), "xml")

    log.debug("Finished parsing XML for " + remote_name)


def parse_all_remote_xml():
    """Parses appstream xml for all remotes"""
    for remote in remotes:
        remote_name = remote.get_name()
        thread = threading.Thread(
            target=parse_remote_xml,
            daemon=True,
            name=remote_name,
            args=(remote_name,)
        )
        xml_parsing_threads[remote_name] = thread
        thread.start()


def get_remote_app(app) -> Flatpak.RemoteRef:
    """Returns a remote instance of the application"""
    log.debug("Getting remote application " + app.get_name())

    remote_name = app.get_origin()
    app_kind = app.get_kind()
    app_name = app.get_name()
    app_branch = app.get_branch()

    return installation.fetch_remote_ref_sync(remote_name, app_kind, app_name, arch, app_branch, None)


def get_installed_app_info(app) -> dict:
    """Returns a dictionary of info about an application"""
    app_info = {
        "id": app.get_name(),
        "name": app.get_appdata_name(),
        "summary": app.get_appdata_summary(),
        "version": app.get_appdata_version(),
        "icon": get_app_icon(app.get_name(), app.get_origin()),
        "size": app.get_installed_size(),
        "size-str": str(round(app.get_installed_size() / 1000000.0, 1)) + " MB"
    }

    return app_info


# def get_app_metadata(app) -> bytes:
#     """Returns an application's metadata"""
#     log.debug("Getting metadata for " + app.get_name())
#
#     if app is Flatpak.InstalledRef:
#         remote_name = app.get_origin()
#         remote_metadata = installation.fetch_remote_metadata_sync(remote_name, app, None)
#     else:
#         remote_metadata = app.get_metadata()
#
#     return remote_metadata.get_data()
#
#
# def parse_remote_metadata(ref) -> dict:
#     """Parses metadata for a remote application"""
#     log.debug("Parsing metadata for " + ref.get_name())
#
#     metadata = get_app_metadata(ref)
#     config.read(metadata)
#     log.debug("Sections: " + str(config.sections()))
#
#     return {}


def get_remote_apps() -> [Flatpak.RemoteRef]:
    """Returns a list of remote applications"""
    log.debug("Getting remote applications")
    remote_apps = []

    for remote in remotes:
        for ref in installation.list_remote_refs_sync(remote.get_name(), None):
            # Only add desktop applications, not runtimes
            if ref.get_kind() is Flatpak.RefKind.APP:
                remote_apps.append(ref)

        log.debug("Remote appstream dir ({}): {}".format(remote.get_name(), remote.get_appstream_dir().get_path()))

    return remote_apps


def get_remote_app_info() -> [dict]:
    """Returns a list of infos about remote apps"""
    app_list = []

    for remote in remotes:
        remote_name = remote.get_name()

        # Get cached xml or read it
        if remote_name not in appstream_xml:
            if remote_name in xml_parsing_threads:
                # Join existing parsing thread
                thread: threading.Thread = xml_parsing_threads[remote_name]
                thread.join()
                del xml_parsing_threads[remote_name]
            else:
                # Wait for function to finish
                parse_remote_xml(remote_name)

        # Store info for each app
        for app in appstream_xml[remote_name].find_all("component", {"type": "desktop"}):
            app_info = {
                "id": app.find("id").text,
                "name": app.find("name").text,
                "summary": app.find("summary").text,
                "size": 0,  # app.get_installed_size()
                "size-str": "",  # str(round(app.get_installed_size() / 1000000.0, 1)) + " MB",
                "icon": get_app_icon(app.find("id").text, remote_name),
                "remote-name": remote_name
            }

            try:
                app_info["version"] = app.find("release").get("version")
            except (KeyError, AttributeError):
                app_info["version"] = "0.0.0"

            app_list.append(app_info)

    log.debug("Generated remote app info")
    return app_list


def get_app_icon_remote(app) -> str:
    """Returns the icon for an application"""
    log.debug("Getting icon for " + app.get_name())

    if type(app) is Flatpak.InstalledRef:
        remote = installation.get_remote_by_name(app.get_origin())
    else:
        remote = installation.get_remote_by_name(app.get_remote_name())

    remote_icon_name = app.get_name() + ".png"
    remote_icon_url = remote.get_url() + "appstream/x86_64/icons/64x64/" + remote_icon_name
    icon_file = path.join(tempdir.name, remote_icon_name)

    # Download icon if not cached
    if not path.exists(icon_file):
        log.debug("Downloading icon for " + app.get_name())
        r = session.get(remote_icon_url, stream=True)
        if r.status_code == 200:
            r.raw.decode_content = True

            with open(icon_file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        else:
            log.warning("Error getting icon for {}, status code {}".format(app.get_name(), r.status_code))

    return icon_file


def get_app_icon_by_name(app_name, remote_name) -> str:
    """Returns the icon for an application"""
    log.debug("Getting icon for " + app_name)

    remote_icon_name = app_name + ".png"
    remote_url = installation.get_remote_by_name(remote_name).get_url()
    remote_icon_url = remote_url + "appstream/x86_64/icons/64x64/" + remote_icon_name
    icon_file = path.join(tempdir.name, remote_icon_name)

    # Download icon if not cached
    if not path.exists(icon_file):
        log.debug("Downloading icon for " + app_name)
        r = session.get(remote_icon_url, stream=True)
        if r.status_code == 200:
            r.raw.decode_content = True

            with open(icon_file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        else:
            log.warning("Error getting icon for {}, status code {}".format(app_name, r.status_code))

    return icon_file


def get_app_icon(app_name, remote_name) -> str:
    """Returns the path of a local app icon"""
    log.debug("Getting local icon path for " + app_name)

    app_icon_file_path = "/var/lib/flatpak/appstream/{}/{}/icons/64x64".format(remote_name, arch)

    if not path.exists(app_icon_file_path):
        app_icon_file_path = "/var/lib/flatpak/appstream/{}/{}/active/icons/64x64".format(remote_name, arch)

    icon_file = "{}/{}.png".format(app_icon_file_path, app_name)

    if not path.exists(icon_file):
        log.warning("Could not find icon for '{}'".format(app_name))

    return icon_file


def update_appstream(remote):
    """Updates the local copy of appstream for remote"""
    remote_name = remote.get_name()
    log.debug("Updating appstream for " + remote_name)

    try:
        installation.update_appstream_full_sync(remote_name, arch, None, None, None)
    except GLib.Error as err:
        log.error(err)
    else:
        log.debug("Updated appstream for " + remote_name)


def get_updates() -> [Flatpak.InstalledRef]:
    """Returns a list of available updates"""
    log.debug("Getting updates")
    return installation.list_installed_refs_for_update(None)


def get_updatable_apps() -> [Flatpak.InstalledRef]:
    """Returns a list of all updatable apps"""
    log.debug("Getting updatable apps")
    updatable_apps = []

    for app in get_updates():
        if app.get_kind() is Flatpak.RefKind.APP:
            updatable_apps.append(app)

    return updatable_apps


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


def cleanup():
    """Cleanup temporary files"""
    log.debug("Cleaning up")
    tempdir.cleanup()
