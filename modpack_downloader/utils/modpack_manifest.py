from enum import StrEnum
from typing import Optional

from pydantic import BaseModel

from modpack_downloader.utils.download_manager import DownloadOptions


class Modloader(StrEnum):
    NEOFORGE = "neoforge"
    FORGE = "forge"
    FABRIC = "fabric"
    QUILT = "quilt"
    LITELOADER = "liteloader"


class ModpackManifest(BaseModel):
    name: str
    version: str
    modlist: list[DownloadOptions]
    minecraft_version: str
    modloader: Modloader
    modloader_version: str
    minecraft_dir: str
    icon: Optional[str] = None


modloader_uid = {
    Modloader.NEOFORGE: "net.neoforged",
    Modloader.FORGE: "net.minecraftforge",
    Modloader.FABRIC: "net.fabricmc.fabric-loader",
    Modloader.QUILT: "org.quiltmc.quilt-loader",
    Modloader.LITELOADER: "com.mumfrey.liteloader"
}
