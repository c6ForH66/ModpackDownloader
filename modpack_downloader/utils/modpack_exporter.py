import threading

from PyQt6.QtCore import pyqtSlot

from modpack_downloader.utils.foreground_task import ForegroundTask
from modpack_downloader.utils.modpack_manifest import ModpackManifest


class MultiMCPackExporter(ForegroundTask):
    def __init__(self, modpack_info: ModpackManifest, parent=None):
        super().__init__(parent)
        self.setObjectName("PackExporterThread")
        self.modpack_info = modpack_info

    @pyqtSlot()
    def run(self):
        threading.current_thread().name = self.objectName()
        raise NotImplementedError
