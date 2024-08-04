import json
import logging
import os
import re
import threading
import urllib.parse
import zipfile

from PyQt6.QtCore import pyqtSlot
from requests import Session, RequestException

from .constants import *
from .download_manager import DownloadOptions
from .foreground_task import ForegroundTask
from .modpack_manifest import Modloader, ModpackManifest
from ..download_options_dialog import InputOptions, ModpackType

logger = logging.getLogger(os.path.basename(__file__))

CF_API_HEAD = {
    "Accept": "application/json",
    "User-Agent": OVERWOLF_UA
}
FTB_API_HEAD = {
    "Accept": "application/json",
    "User-Agent": OVERWOLF_UA
}


class ModpackResolver(ForegroundTask):
    def __init__(self, download_options: InputOptions, session: Session, parent=None):
        super().__init__(parent)
        self.setObjectName("ModpackResolverThread")
        self.download_options = download_options
        self.session = session
        self.completed_num = 0
        self.total_num = 0

    @pyqtSlot()
    def run(self):
        threading.current_thread().name = self.objectName()
        self.progress_changed.emit(0, 0)
        match self.download_options.modpack_type:
            case ModpackType.CF_LOCAL:
                self.local_cf_pack()
            case ModpackType.CF_ONLINE:
                raise NotImplementedError
            case ModpackType.FTB:
                self.ftb_modpack()

    def _get_modpack_files(self, manifest: dict):
        payload = []
        for file in manifest["files"]:
            payload.append(file["fileID"])
        resp = self.session.post(CF_GET_FILES_URL, json={"fileIds": payload}, headers=CF_API_HEAD)
        resp.raise_for_status()
        return resp.json()

    def _ftb_manifest(self) -> tuple[dict, dict]:
        self.status.emit("Fetching modpack manifest")
        modpack_mf_resp = self.session.get(FTB_MODPACK_MF_URL.format(self.download_options.modpack_id),
                                           headers=FTB_API_HEAD)
        modpack_mf = modpack_mf_resp.json()
        self.progress_changed.emit(1, 2)
        self.status.emit("Fetching version manifest")
        version_mf_resp = self.session.get(
            FTB_VERSION_MF_URL.format(self.download_options.modpack_id, self.download_options.version_id),
            headers=FTB_API_HEAD)
        version_mf = version_mf_resp.json()
        self.progress_changed.emit(2, 2)
        return modpack_mf, version_mf

    def ftb_modpack(self):
        try:
            modpack_mf, version_mf = self._ftb_manifest()
        except RequestException as e:
            logger.error("Failed to resolve modpack", exc_info=e)
            self.failed.emit("Failed to resolve modpack")
            return

        if modpack_mf["status"] != "success":
            logger.error(modpack_mf["message"])
            self.failed.emit(modpack_mf["message"])
            return

        if version_mf["status"] != "success":
            logger.error(version_mf["message"])
            self.failed.emit(version_mf["message"])
            return

        name = modpack_mf["name"]
        version = version_mf["name"]
        mc_version = ""
        modloader = ""
        modloader_version = ""
        for target in version_mf["targets"]:
            if target["type"] == "game":
                mc_version = target["version"]
            elif target["type"] == "modloader":
                modloader = Modloader(target["name"])
                modloader_version = target["version"]

        icon_url = None
        task_list = []
        for art in modpack_mf["art"]:
            if art["type"] == "square":
                icon_url = art["url"]
                break

        folder_name = re.sub(r"[\\/:*?\"<>|]", "", name)  # remove invalid chars
        minecraft_dir = os.path.join(self.download_options.save_dir, folder_name)

        os.makedirs(minecraft_dir, exist_ok=True)

        icon_filename = None
        if icon_url:
            icon_filename = (re.sub(r"[\\/:*?\"><|\s]", "_", name.lower())
                             + os.path.splitext(urllib.parse.urlparse(icon_url).path)[1])

            task_list.append(DownloadOptions(url=icon_url, dir=minecraft_dir, out=icon_filename))

        else:
            logger.warning(f"Unable to find modpack icon for modpack f{name}")

        for file in version_mf["files"]:
            if file["size"] == 0:
                continue
            out_dir = os.path.abspath(os.path.join(minecraft_dir, file["path"]))
            task = DownloadOptions(url=file["url"],
                                   dir=out_dir,
                                   out=file["name"],
                                   checksum=f"sha-1={file['sha1']}")

            task_list.append(task)

        modpack_info = ModpackManifest(name=name, version=version, modlist=task_list, minecraft_version=mc_version,
                                       modloader=modloader,
                                       modloader_version=modloader_version, minecraft_dir=minecraft_dir,
                                       icon=icon_filename)

        self.complete.emit(modpack_info)

    # TODO: Search and download the icon of curseforge modpacks
    def search_modpack_icon(self, name: str, modpack_id: int):
        pass

    def local_cf_pack(self):
        api_key = os.environ.get("CF_API_KEY")
        if api_key is None:
            self.failed.emit("Curseforge API key not found")
            return

        CF_API_HEAD.update({"x-api-key": api_key})

        archive_name = os.path.basename(self.download_options.local_modpack_file)
        extract_dir = os.path.join(self.download_options.save_dir, os.path.splitext(archive_name)[0])
        minecraft_dir = os.path.join(extract_dir, "overrides")

        self.status.emit("Extracting modpack")
        os.makedirs(extract_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(self.download_options.local_modpack_file) as f:
                f.extractall(extract_dir)

            with open(os.path.join(extract_dir, "manifest.json")) as f:
                manifest = json.load(f)

        except (IOError, zipfile.BadZipFile, json.JSONDecodeError) as e:
            logger.error("Failed to resolve modpack", exc_info=e)
            self.failed.emit("Failed to read manifest, the modpack might be broken")
            return

        try:
            assert manifest["manifestType"] == "minecraftModpack", "Not a minecraft modpack"
            name = manifest["name"]
            version = manifest["version"]
            mc_version = manifest["minecraft"]["version"]
            modloader, modloader_version = manifest["minecraft"]["modLoaders"][0]["id"].split("-")

            self.total_num = len(manifest["files"])
            self.status.emit("Resolving mod download links")
            result = self._get_modpack_files(manifest)
            modlist = []
            file_ids = []
            for mod_file in result["data"]:
                # I don't know what the hell are they doing, but the api randomly returns repeated results?!
                if mod_file["id"] in file_ids:
                    logger.warning(f"Found repeated mods: {mod_file['id']}")
                    continue
                file_ids.append(mod_file["id"])
                sha1 = mod_file["hashes"][0]["value"]
                modlist.append(
                    DownloadOptions(url=mod_file["downloadUrl"], dir=os.path.join(minecraft_dir, "mods"),
                                    out=mod_file["fileName"], checksum=f"sha-1={sha1}"))

            modpack_info = ModpackManifest(name=name, version=version, modlist=modlist, minecraft_version=mc_version,
                                           modloader=modloader,
                                           modloader_version=modloader_version, minecraft_dir=minecraft_dir,
                                           icon=None)

            self.complete.emit(modpack_info)

        except (KeyError, AssertionError) as e:
            logger.error("Failed to resolve modpack", exc_info=e)
            self.failed.emit("Manifest file is broken or it's not a minecraft modpack")

        except RequestException as e:
            logger.error("Failed to resolve modpack", exc_info=e)
            self.failed.emit("Failed to resolve modpack")
