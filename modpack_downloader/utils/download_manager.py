import functools
import logging
import os
import re
from typing import Literal

from PyQt6.QtCore import *
from pydantic import BaseModel, ConfigDict, field_validator, TypeAdapter

from ..rpc.client import Aria2Client, MulticallClient
from ..rpc.event_listener import Aria2EventListener

logger = logging.getLogger(os.path.basename(__file__))


class DownloadOptions(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: re.sub("_", "-", field_name))
    url: str
    dir: str
    out: str = ""
    checksum: str = ""


class A2Task(BaseModel):
    gid: str
    status: Literal["active", "waiting", "paused", "error", "complete", "removed"] = "waiting"
    totalLength: int = 0
    completedLength: int = 0
    downloadSpeed: int = 0
    files: list = []
    errorMessage: str = ""

    @property
    def name(self):
        return os.path.basename(self.files[0]["path"])

    @property
    def progress(self) -> int:
        if self.status == "complete":
            return 100
        if self.totalLength == 0:
            return 0
        return int(self.completedLength / self.totalLength * 100)

    # noinspection PyNestedDecorators
    field_validator("totalLength", "completedLength", "downloadSpeed", mode="before")(lambda x: int(x))


class DownloadManager(QObject):
    RETRY_INTERVAL = 5000
    UPDATE_INTERVAL = 200

    task_updated = pyqtSignal()
    download_complete = pyqtSignal()
    progress_changed = pyqtSignal(int, int)

    _ta = TypeAdapter(list[A2Task])

    start = pyqtSignal(list)
    stop = pyqtSignal()

    def __init__(self, client: Aria2Client, event_listener: Aria2EventListener):
        super().__init__()
        self.client = client
        self.multicall = MulticallClient(self.client)
        self.event_listener = event_listener
        self.downloading = False
        self.timer = QTimer()
        self.task_list: list[A2Task] = []
        self.event_listener.onDownloadComplete.connect(self.mod_complete)
        self.event_listener.onDownloadError.connect(self.download_error)
        self.stop.connect(self.shutdown)
        self.start.connect(self.start_download_modpack)
        self.total_mods = 0
        self.completed_mods = 0
        self.retry_counter = {}

    def run(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)

    @pyqtSlot(list)
    def start_download_modpack(self, modlist: list[DownloadOptions]):
        logger.info("Starting download")
        if self.downloading:
            logger.warning("already downloading a modpack!")
            return
        self.client.purge_download_result()
        self.completed_mods = 0
        self.total_mods = len(modlist)
        self.retry_counter = {}
        for task in modlist:
            self.multicall.add_uri([task.url], task.dict(exclude={"url"}, exclude_defaults=True))
        self.multicall.multicall()
        self.timer.start(self.UPDATE_INTERVAL)
        self.downloading = True

    @pyqtSlot(str)
    def download_error(self, gid: str):
        g = self.client.tell_status(gid)
        uri = g["files"][0]["uris"][0]["uri"]
        if uri not in self.retry_counter:
            self.retry_counter[uri] = 1
        else:
            self.retry_counter[uri] += 1
        logger.error(f"{uri} download failed. ({self.retry_counter[uri]}/5 attempts)")
        if self.retry_counter[uri] < 5:
            QTimer.singleShot(self.RETRY_INTERVAL, functools.partial(self.client.restart_download, gid))

    @pyqtSlot()
    def retry_all(self):
        if not self.downloading:
            return
        self.client.retry_all()
        self.retry_counter = {}

    @pyqtSlot(str)
    def mod_complete(self, gid: str):
        self.completed_mods += 1
        logger.info(gid + f" completed {self.completed_mods}/{self.total_mods}")
        self.progress_changed.emit(self.completed_mods, self.total_mods)

        if self.completed_mods == self.total_mods:
            self.downloading = False
            logger.info("download complete")
            self.download_complete.emit()
            self.refresh_data()
            self.timer.stop()

    @pyqtSlot()
    def refresh_data(self):
        self.task_list = self._ta.validate_python(self.client.get_all_downloads())
        self.task_updated.emit()

    @pyqtSlot()
    def shutdown(self):
        self.timer.stop()
        self.client.shutdown()
