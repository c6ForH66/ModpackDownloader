import json
import logging
import os
import pprint
import re
import threading
import urllib.parse
import zipfile
from enum import IntEnum

from PyQt6.QtCore import pyqtSlot
from requests import Session, RequestException

from .constants import *
from .download_manager import DownloadOptions
from .foreground_task import ForegroundTask
from .modpack_manifest import Modloader, ModpackManifest
from ..new_download_dialog import InputOptions, ModpackType

logger = logging.getLogger(os.path.basename(__file__))

CF_API_HEAD = {
    "Accept": "application/json",
    "User-Agent": OVERWOLF_UA
}
FTB_API_HEAD = {
    "Accept": "application/json",
    "User-Agent": OVERWOLF_UA
}


class FileType(IntEnum):
    MOD = 6
    RESOURCEPACK = 12
    SHADER = 6552


SUBFOLDER = {
    FileType.MOD: "mods",
    FileType.RESOURCEPACK: "resourcepacks",
    FileType.SHADER: "shaderpacks"
}


class ModpackResolver(ForegroundTask):
    def __init__(self, download_options: InputOptions, session: Session, parent=None):
        super().__init__(parent)
        self.setObjectName("ModpackResolverThread")
        self.download_options = download_options
        self.session = session

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

    @staticmethod
    def _get_file_hash(mod_file: dict) -> str:
        algo = None
        hash_value = None
        for hash_item in mod_file["hashes"]:
            if hash_item["algo"] == 1:
                algo = "sha-1"
                hash_value = hash_item["value"]
                break
            elif hash_item["algo"] == 2:
                algo = "md5"
                hash_value = hash_item["value"]
                break
        hash_arg = f"{algo}={hash_value}" if algo else None
        return hash_arg

    def _get_modpack_files(self, manifest: dict) -> tuple[list[dict], dict[str, FileType]]:
        file_list = []
        mod_list = []
        modid_fileid_mapping = dict()
        fileid_type_mapping = dict()
        for file in manifest["files"]:
            file_id = file["fileID"]
            modid = file["projectID"]
            modid_fileid_mapping[modid] = file_id
            file_list.append(file_id)
            mod_list.append(modid)

        resp = self.session.post(CF_GET_FILES_URL, json={"fileIds": file_list}, headers=CF_API_HEAD)
        resp.raise_for_status()
        file_info = resp.json()["data"]

        resp = self.session.post(CF_GET_MODS_URL, json={"modIds": mod_list}, headers=CF_API_HEAD)
        resp.raise_for_status()
        mod_info = resp.json()["data"]

        for mod_file in mod_info:
            mod_type = FileType(int(mod_file["classId"]))
            modid = mod_file["id"]
            fileid = modid_fileid_mapping[modid]
            fileid_type_mapping[fileid] = mod_type

        return file_info, fileid_type_mapping

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
            icon_suffix = os.path.splitext(urllib.parse.urlparse(icon_url).path)[1]
            icon_filename = re.sub(r"[\\/:*?\"><|\s]", "_", name.lower()) + icon_suffix

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

        logger.info("Extracting modpack file: %s", archive_name)
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

            self.status.emit("Resolving mod download links")
            file_info, mapping = self._get_modpack_files(manifest)

            task_list = []
            for mod_file in file_info:
                file_id = mod_file["id"]
                hash_arg = self._get_file_hash(mod_file)
                subdir = SUBFOLDER[mapping[file_id]]
                out_dir = os.path.abspath(os.path.join(minecraft_dir, subdir))

                task_list.append(DownloadOptions(url=mod_file["downloadUrl"], dir=out_dir,
                                                 out=mod_file["fileName"], checksum=hash_arg))

            modpack_info = ModpackManifest(name=name, version=version, modlist=task_list,
                                           minecraft_version=mc_version, modloader=modloader,
                                           modloader_version=modloader_version,
                                           minecraft_dir=minecraft_dir, icon=None)

            self.complete.emit(modpack_info)

        except (KeyError, AssertionError) as e:
            logger.error("Failed to resolve modpack", exc_info=e)
            self.failed.emit("Manifest file is broken or it's not a minecraft modpack")

        except Exception as e:
            logger.error("Unknown error resolving modpack files", exc_info=e)
            self.failed.emit("Failed to resolve modpack")
