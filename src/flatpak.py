import gzip
import logging
import threading
import gi

gi.require_version('Flatpak', '1.0')

from gi.repository import GLib, Flatpak
from os import path
from bs4 import BeautifulSoup

installation: Flatpak.Installation = Flatpak.get_system_installations()[0]
default_arch: str = Flatpak.get_default_arch()
log: logging.Logger = logging.getLogger('Flati.flatpak')
appstream_xml = {}
xml_parsing_threads: {str, threading.Thread} = {}


def get_remotes() -> [Flatpak.Remote]:
    """Returns a list of currently enabled remotes (http(s) only, not OCI)"""
    all_remotes: [Flatpak.Remote] = installation.list_remotes()

    remote_list = []
    for remote in all_remotes:
        remote_url = remote.get_url()
        if not remote_url.startswith("oci+") and not remote.get_disabled():
            remote_list.append(remote)

    return remote_list


def update_remote_info():
    """Updates local configuration and appstream for all enabled http(s) remotes"""
    log.debug("Updating local configuration for all remotes")

    for remote in get_remotes():
        remote_name = remote.get_name()
        try:
            installation.update_remote_sync(remote_name, None)
            installation.update_appstream_sync(remote_name, default_arch, None, None)
        except GLib.Error as err:
            log.error(err)


def parse_remote_xml(remote_name: str):
    """Parses appstream of a remote to get info about its applications"""
    # Don't parse the XML file again, if it has already been parsed
    if remote_name in appstream_xml:
        return

    log.debug("Parsing XML for '{}'".format(remote_name))
    xml_path = installation \
        .get_remote_by_name(remote_name) \
        .get_appstream_dir() \
        .get_path()
    log.debug("Appstream directory for '{}': {}".format(remote_name, xml_path))
    xml_file = xml_path + "/appstream.xml"

    # Open appstream.xml if it exists, otherwise open appstream.xml.gz
    if path.exists(xml_file):
        with open(xml_file, 'rb') as xml:
            appstream_xml[remote_name] = BeautifulSoup(xml, "xml")
    else:
        xml_file = xml_path + "/appstream.xml.gz"
        if path.exists(xml_file):
            with gzip.open(xml_file, 'rb') as xml:
                appstream_xml[remote_name] = BeautifulSoup(xml, "xml")
        else:
            log.error("XML file for '{}' not found!".format(remote_name))

    log.info("Finished parsing XML for '{}'".format(remote_name))


def parse_all_remote_xmls():
    """Wrapper around parse_remote_xml to parse appstream for all remotes in parallel"""
    for remote in get_remotes():
        remote_name = remote.get_name()
        thread_name = "AppstreamParser_" + remote_name
        thread = threading.Thread(
            target=parse_remote_xml,
            daemon=True,
            name=thread_name,
            args=(remote_name,)
        )

        xml_parsing_threads[thread_name]: threading.Thread = thread
        thread.start()


def get_remote_ref(ref: Flatpak.Ref) -> Flatpak.RemoteRef:
    """Returns a RemoteRef object of a (Installed)Ref"""
    remote_name = ref.get_origin()
    app_kind = ref.get_kind()
    app_name = ref.get_name()
    app_branch = ref.get_branch()

    log.debug("Getting RemoteRef for '{}'".format(app_name))
    return installation.fetch_remote_ref_sync(
        remote_name,
        app_kind,
        app_name,
        default_arch,
        app_branch,
        None
    )


def get_installed_ref_info(ref: Flatpak.InstalledRef) -> dict:
    """Returns info about an installed application"""
    return {
        # From Flatpak.Ref
        "arch": ref.get_arch(),
        "branch": ref.get_branch(),
        "collection-id": ref.get_collection_id(),
        "commit": ref.get_commit(),
        "kind": ref.get_kind(),
        "id": ref.get_name(),

        # From Flatpak.InstalledRef
        "content-rating": ref.get_appdata_content_rating(),
        "content-rating-type": ref.get_appdata_content_rating_type(),
        "license": ref.get_appdata_license(),
        "name": ref.get_appdata_name(),
        "summary": ref.get_appdata_summary(),
        "version": ref.get_appdata_version(),
        "deploy-dir": ref.get_deploy_dir(),
        "eol": ref.get_eol(),
        "eol-rebase": ref.get_eol_rebase(),
        "size": ref.get_installed_size(),
        "is-current": ref.get_is_current(),
        "latest-commit": ref.get_latest_commit(),
        "remote": ref.get_origin(),
        "subpaths": ref.get_subpaths(),

        # Extra
        "size-str": str(round(ref.get_installed_size() / 1000000.0, 1)) + " MB",
        "icon": get_app_icon(ref.get_name(), ref.get_origin()),
        "ref": ref,
    }


def get_installed_apps_info() -> [dict]:
    """Returns info about installed applications"""
    info_list: [{}] = []
    app_list = get_installed_apps()

    app: Flatpak.InstalledRef
    for app in app_list:
        info_list.append(get_installed_ref_info(app))

    return info_list


def get_updatable_apps_info() -> [dict]:
    """Returns info about updatable apps"""
    info_list: [{}] = []
    app_list = get_updatable_apps()

    app: Flatpak.InstalledRef
    for app in app_list:
        info_list.append(get_installed_ref_info(app))

    return info_list


def get_remote_apps_info() -> [dict]:
    """Returns info about remote applications"""
    app_list: [{}] = []

    for remote in get_remotes():
        remote_name = remote.get_name()
        thread_name = "AppstreamParser_" + remote_name

        # Get info from previously parsed XML or wait for it to be parsed
        if remote_name not in appstream_xml:
            if thread_name in xml_parsing_threads:
                # Join existing parsing thread
                thread: threading.Thread = xml_parsing_threads[thread_name]
                thread.join()

                # Delete thread reference from list of running threads
                del xml_parsing_threads[thread_name]
            else:
                # Wait for function to finish
                parse_remote_xml(remote_name)

        # Store info for each app
        for app in appstream_xml[remote_name].find_all("component", {"type": "desktop"}):
            app_id = app.find("id").text
            app_branch = app.find("bundle").text.split("/")[-1]

            remote_ref: Flatpak.RemoteRef
            try:
                remote_ref = installation.fetch_remote_ref_sync(
                    remote_name,
                    Flatpak.RefKind.APP,
                    app_id,
                    default_arch,
                    app_branch,
                    None
                )
            except GLib.GError as err:
                # log.info("Could not get remote ref for '{}': {}".format(app_id, err))
                continue

            app_info = {
                # From appstream file
                "id": app_id,
                "name": app.find("name").text,
                "summary": app.find("summary").text,
                "description": app.find("description").text,

                # From Flatpak.RemoteRef
                "arch": remote_ref.get_arch(),
                "branch": remote_ref.get_branch(),
                "collection-id": remote_ref.get_collection_id(),
                "commit": remote_ref.get_commit(),
                "kind": remote_ref.get_kind(),
                "size": remote_ref.get_download_size(),
                "eol": remote_ref.get_eol(),
                "eol-rebase": remote_ref.get_eol_rebase(),
                "remote": remote_ref.get_remote_name(),

                # Extra
                "size-str": str(round(remote_ref.get_download_size() / 1000000.0, 1)) + " MB",
                "icon": get_app_icon(app_id, remote_name),
                "ref": remote_ref,
            }

            # Version might not be present in appstream file
            try:
                app_info["version"] = app.find("release").get("version")
            except (KeyError, AttributeError):
                app_info["version"] = ""

            app_list.append(app_info)

    log.debug("Generated remote app info")
    return app_list


def get_app_icon(app_id: str, remote_name: str) -> str:
    """Returns the path of an app icon file"""
    log.debug("Getting local icon path for '{}'".format(app_id))

    appstream_path = installation \
        .get_remote_by_name(remote_name) \
        .get_appstream_dir() \
        .get_path()
    icon_file = "{}/icons/64x64/{}.png".format(appstream_path, app_id)
    if not path.exists(icon_file):
        log.info("Could not find icon for '{}'".format(app_id))

    # Return path even if icon is missing, since GTK will replace it with a broken icon
    return icon_file


def get_updates() -> [Flatpak.InstalledRef]:
    """Returns a list of refs with available updates"""
    log.debug("Getting updatable refs")
    return installation.list_installed_refs_for_update(None)


def get_installed_apps() -> [Flatpak.InstalledRef]:
    """Returns a list of installed applications"""
    log.debug("Getting installed applications")
    return installation.list_installed_refs_by_kind(Flatpak.RefKind.APP, None)


def get_updatable_apps() -> [Flatpak.InstalledRef]:
    """Returns a list of applications with available updates"""
    log.debug("Getting updatable applications")
    updatable_apps = []

    for app in get_updates():
        if app.get_kind() is Flatpak.RefKind.APP:
            updatable_apps.append(app)

    return updatable_apps


def get_remote_apps() -> [Flatpak.RemoteRef]:
    """Returns a list of remote applications"""
    log.debug("Getting remote applications")
    remote_apps = []

    for remote in get_remotes():
        for ref in installation.list_remote_refs_sync(remote.get_name(), None):
            # Only add desktop applications, not runtimes
            if ref.get_kind() is Flatpak.RefKind.APP:
                remote_apps.append(ref)

    return remote_apps


def install_local_ref(ref_path: str):
    """Installs a ref from a .flatpakref file"""
    ref_id = path.basename(ref_path)
    log.debug("Installing '{}'".format(ref_id))

    with open(ref_path, 'rb') as file:
        ref_data = GLib.Bytes.new(file.read())
        try:
            transaction: Flatpak.Transaction = Flatpak.Transaction \
                .new_for_installation(installation, None)
            transaction.add_install_flatpakref(ref_data)
            transaction.run()
        except GLib.Error as err:
            log.error(err)
        else:
            log.debug("Installed '{}'".format(ref_id))


def install_remote_ref(ref_id: str, remote_name: str):
    """Installs a ref based on its id and remote"""
    try:
        transaction: Flatpak.Transaction = Flatpak.Transaction \
            .new_for_installation(installation, None)
        transaction.add_install(remote_name, ref_id, None)
        transaction.run()
    except GLib.Error as err:
        log.error(err)


def update_ref(ref: Flatpak.InstalledRef):
    """Updates an installed ref"""
    log.debug("Updating '{}'".format(ref.get_name()))

    try:
        transaction: Flatpak.Transaction = Flatpak.Transaction \
            .new_for_installation(installation, None)
        transaction.add_update(ref.format_ref(), None, None)
        transaction.run()
    except GLib.Error as err:
        log.error(err)
    else:
        log.debug("Updated '{}'".format(ref.get_name()))


def update_all_refs():
    """Updates all installed refs"""
    log.debug("Updating all installed refs")
    [update_ref(ref) for ref in get_updates()]


def uninstall_ref(ref: Flatpak.InstalledRef):
    """Uninstalls an installed ref"""
    log.debug("Uninstalling '{}'".format(ref.get_name()))

    try:
        transaction = Flatpak.Transaction.new_for_installation(installation, None)
        transaction.add_uninstall(ref.format_ref())
        transaction.run()
    except GLib.Error as err:
        log.error(err)
    else:
        log.debug("Uninstalled '{}'".format(ref.get_name()))
