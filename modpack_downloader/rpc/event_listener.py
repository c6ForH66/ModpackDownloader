import json
import logging
import os

from PyQt6.QtCore import *
from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect

from .client import Aria2Client

__all__ = ["Aria2EventListener"]

logger = logging.getLogger(os.path.basename(__file__))


class Aria2EventListener(QThread):
    onDownloadStart = pyqtSignal(str)
    onDownloadPause = pyqtSignal(str)
    onDownloadStop = pyqtSignal(str)
    onDownloadComplete = pyqtSignal(str)
    onDownloadError = pyqtSignal(str)
    onBtDownloadComplete = pyqtSignal(str)

    def __init__(self, client: Aria2Client):
        super().__init__()
        self.client = client

    def run(self):
        ws = connect(self.client.ws_server, ping_interval=None)
        logger.info("Started listening to notifications")
        while True:
            try:
                msg = ws.recv()
                self.process_notification(json.loads(msg))
            except ConnectionClosed:
                logger.warning("Connection closed")
                return
            except Exception as e:
                logger.error("Unexpected error: %s", e)

    def process_notification(self, msg: dict):
        event = msg["method"]
        gid = msg["params"][0]["gid"]
        match event:
            case "aria2.onDownloadStart":
                self.onDownloadStart.emit(gid)
            case "aria2.onDownloadPause":
                self.onDownloadPause.emit(gid)
            case "aria2.onDownloadStop":
                self.onDownloadStop.emit(gid)
            case "aria2.onDownloadComplete":
                self.onDownloadComplete.emit(gid)
            case "aria2.onDownloadError":
                self.onDownloadError.emit(gid)
            case "aria2.onBtDownloadComplete":
                self.onBtDownloadComplete.emit(gid)
