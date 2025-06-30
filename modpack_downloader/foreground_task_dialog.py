import logging
import os.path

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from .ui.ui_foreground_task import Ui_ForegroundTaskDialog
from .utils.foreground_task import ForegroundTask

__all__ = "ForegroundTaskDialog"

logger = logging.getLogger(os.path.basename(__file__))


class ForegroundTaskDialog(QDialog, Ui_ForegroundTaskDialog):

    def __init__(self, util: ForegroundTask, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.rejected.connect(self.cancel)
        self.return_data = None

        self.util = util
        self.util_thread = QThread()
        self.util.moveToThread(self.util_thread)
        self.util.complete.connect(self.complete)
        self.util.progress_changed.connect(self.update_status)
        self.util.failed.connect(self.show_error)
        self.util.status.connect(self.label.setText)

        self.util_thread.started.connect(self.util.run)
        self.util_thread.start()

    @pyqtSlot(str)
    def show_error(self, msg: str):
        QMessageBox.critical(self, self.windowTitle(), msg)
        self.reject()

    @pyqtSlot(int, int)
    def update_status(self, n, m):
        self.progressBar.setMaximum(m)
        self.progressBar.setValue(n)
        self.label_progress.setText(f"{n}/{m}")

    @pyqtSlot(object)
    def complete(self, r):
        self.return_data = r
        self.util_thread.quit()
        self.util_thread.wait()
        self.accept()

    def cancel(self):
        self.util_thread.terminate()
        self.util_thread.wait()



