#!/usr/bin/python3

import logging
import os
import sys

from PyQt6.QtWidgets import *
from modpack_downloader.main_window import MainWindow

logger = logging.getLogger(os.path.basename(__file__))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="[%(asctime)s] [%(name)-s] [%(threadName)s] [%(levelname)-s] %(message)s")

    app = QApplication(sys.argv)
    if os.environ.get("CF_API_KEY") is None:
        try:
            from api_key import CF_API_KEY
        except ImportError:
            QMessageBox.critical(None, "Error", "Cannot find curseforge api key")
            sys.exit(1)
        os.environ["CF_API_KEY"] = CF_API_KEY

    logger.info("Curseforge api key loaded")

    w = MainWindow()
    w.show()
    app.exec()
