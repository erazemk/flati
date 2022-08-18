import logging
import gi
import tempfile
import requests
import shutil
import configparser
import gzip

gi.require_version('Flatpak', '1.0')

from gi.repository import GLib, Flatpak
from os import path
from bs4 import BeautifulSoup

installation = Flatpak.get_system_installations()[0]
arch = Flatpak.get_default_arch()
remotes = installation.list_remotes()
session = requests.Session()
log = logging.getLogger('flatpak')
tempdir = tempfile.TemporaryDirectory()
config = configparser.ConfigParser()
xml = {}


def sync_remotes():
    """Sync all system remotes"""
    log.debug("Syncing remotes")

    for remote in remotes:
        try:
            installation.update_remote_sync(remote.get_name(), None)
        except GLib.Error as err:
            log.error(err)


def parse_remote_xml(remote):
    """Parses appstream xml for a remote"""
    xml_path = installation.get_remote_by_name(remote).get_appstream_dir().get_path()
    xml_file = xml_path + "/active/appstream.xml.gz"

    if not path.exists(xml_file):
        xml_file = xml_path + "/appstream.xml.gz"

    if not path.exists(xml_file):
        log.error("XML file for {} not found!".format(remote))

    if remote not in xml:
        with gzip.open(xml_file, 'rb') as f:
            xml[remote] = BeautifulSoup(f.read(), "xml")


def parse_all_remote_xml():
    """Parses appstream xml for all remotes"""
    for remote in remotes:
        if remote.get_disabled() is False:
            parse_remote_xml(remote.get_name())


def get_remote_app(app) -> Flatpak.RemoteRef:
    """Returns a remote application"""
    log.debug("Getting remote application " + app.get_name())

    remote_name = app.get_origin()
    kind = app.get_kind()
    name = app.get_name()
    branch = app.get_branch()

    return installation.fetch_remote_ref_sync(remote_name, kind, name, arch, branch, None)


def get_app_info(app) -> dict:
    """Returns a dictionary of info about an application"""
    app_info = {}

    if type(app) is Flatpak.InstalledRef:  # InstalledRef, just extract info
        app_info["id"] = app.get_name()
        app_info["name"] = app.get_appdata_name()
        app_info["summary"] = app.get_appdata_summary()
        app_info["version"] = app.get_appdata_version()
    else:  # RemoteRef, need to read appstream
        app_id = app.get_name()
        remote = app.get_origin()

        # Get cached xml or read it
        if remote not in xml:
            parse_remote_xml(remote)

        app_xml = xml[remote].find_all(lambda tag: tag.name == "id" and app_id in tag.text)[0].parent

        app_info["id"] = app_xml.find("id").text
        app_info["name"] = app_xml.find("name").text
        app_info["summary"] = app_xml.find("summary").text
        app_info["version"] = app_xml.find("release").get("version")

    app_info["icon"] = get_app_icon(app)
    app_info["size"] = app.get_installed_size()
    app_info["size_str"] = str(round(app.get_installed_size() / 1000000.0, 1)) + " MB"

    return app_info


def get_app_metadata(app) -> bytes:
    """Returns an application's metadata"""
    log.debug("Getting metadata for " + app.get_name())

    if app is Flatpak.InstalledRef:
        remote_name = app.get_origin()
        remote_metadata = installation.fetch_remote_metadata_sync(remote_name, app, None)
    else:
        remote_metadata = app.get_metadata()

    return remote_metadata.get_data()


def parse_remote_metadata(ref) -> dict:
    """Parses metadata for a remote application"""
    log.debug("Parsing metadata for " + ref.get_name())

    metadata = get_app_metadata(ref)
    config.read(metadata)
    log.debug("Sections: " + str(config.sections()))

    return {}


def get_remote_apps() -> [Flatpak.RemoteRef]:
    """Returns a list of remote applications"""
    log.debug("Getting remote applications")
    remote_apps = []

    for remote in remotes:
        if remote.get_disabled() is False:
            remote_apps.extend(installation.list_remote_refs_sync(remote.get_name(), None))
            installation.update_appstream_sync(remote.get_name(), arch, None, None)
            log.debug("Remote appstream dir ({}): {}".format(remote.get_name(), remote.get_appstream_dir().get_path()))

    return remote_apps


def get_app_icon(app) -> str:
    """Returns the icon for an application"""
    log.debug("Getting icon for " + app.get_name())

    remote = installation.get_remote_by_name(app.get_origin())
    remote_icon_url = remote.get_url() + "appstream/" + app.get_arch() + "/icons/64x64/" + app.get_name() + ".png"
    filename = remote_icon_url.split('/')[-1]
    file = path.join(tempdir.name, filename)

    # Download icon if not cached
    if not path.exists(file):
        log.debug("Downloading icon for " + app.get_name())
        r = session.get(remote_icon_url, stream=True)
        if r.status_code == 200:
            r.raw.decode_content = True

            with open(file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        else:
            log.warning("Error getting icon for {}, status code {}".format(app.get_name(), r.status_code))

    return file


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
