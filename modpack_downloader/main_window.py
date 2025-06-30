import functools
import logging
import os
import shutil
import sys
import time
from configparser import ConfigParser

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from packaging.version import Version
from requests import Session

from .new_download_dialog import *
from .download_table_view import A2TaskModel
from .foreground_task_dialog import ForegroundTaskDialog
from .rpc.client import Aria2Client
from .rpc.event_listener import Aria2EventListener
from .ui.ui_main_window import Ui_MainWindow
from .utils.download_manager import DownloadManager
from .utils.modpack_exporter import MultiMCPackExporter
from .utils.modpack_manifest import ModpackManifest
from .utils.modpack_resolver import ModpackResolver

logger = logging.getLogger(os.path.basename(__file__))


class ProgressDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        progress = index.data(Qt.ItemDataRole.DisplayRole)
        opt = QStyleOptionProgressBar()
        opt.rect = option.rect
        opt.minimum = 0
        opt.maximum = 100
        opt.progress = progress
        opt.text = f"{progress}%"
        opt.textVisible = True
        QApplication.style().drawControl(QStyle.ControlElement.CE_ProgressBar, opt, painter)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.task_gids = []

        self.actionExit.triggered.connect(self.close)
        self.actionDownload.triggered.connect(self.download_modpack)

        self.session = Session()

        logger.info("Reading aria2 config file")

        conf_file = os.path.join(os.path.dirname(sys.argv[0]), "aria2.conf")
        parser = ConfigParser()
        with open(conf_file) as f:
            parser.read_string("[DEFAULT]\n"+f.read())

        port = int(parser["DEFAULT"].get("rpc-listen-port", "6800"))
        logger.info(f"Aria2 port: {port}")

        self.aria2_args = ["--conf-path", conf_file, "--stop-with-process", str(os.getpid()),
                           "--log=aria2.log", "--log-level=debug"]

        logger.info("Locating aria2 executable")

        if os.name == "nt":
            a2_exe = shutil.which("aria2c.exe")
        elif os.name == "posix":
            a2_exe = shutil.which("aria2c")
        else:
            QMessageBox.critical(self, self.windowTitle(), "Unsupported platform")
            sys.exit(1)
        if a2_exe is None:
            QMessageBox.critical(self, self.windowTitle(), "Aria2 executable not found, please install aria2")
            sys.exit(1)

        logger.info(f"Aria2 executable found: {a2_exe}")

        self.aria2 = QProcess()
        self.aria2.setProgram(a2_exe)
        self.aria2.setArguments(self.aria2_args)
        self.aria2.start()

        if not self.aria2.waitForStarted():
            QMessageBox.critical(self, self.windowTitle(), "Failed to start aria2")
            sys.exit(1)

        time.sleep(1)
        self.client = Aria2Client(port=port, session=self.session)
        min_version = Version("1.37.0")
        try:
            version = Version(self.client.get_version()["version"])
            logger.info(f"Aria2 version: {version}")
            if version < min_version:
                logger.critical(f"Aria2 below 1.37.0 (currently installed {version}) wont work")
                QMessageBox.critical(self, self.windowTitle(),
                                     f"Aria2 below 1.37.0 (currently installed {version}) wont work.\n"
                                     "Please upgrade aria2.")
                sys.exit(1)

        except Exception as e:
            logger.critical("Failed to get aria2 version,exiting...", exc_info=e)
            sys.exit(1)

        self.event_listener = Aria2EventListener(self.client)

        self.task_manager_thread = QThread()
        self.task_manager = DownloadManager(self.client, self.event_listener)
        self.task_manager.moveToThread(self.task_manager_thread)
        self.task_manager_thread.started.connect(self.task_manager.run)
        self.task_manager.destroyed.connect(self.task_manager_thread.quit)
        self.task_manager.progress_changed.connect(self.update_pbar)

        self.button_restart_failed.clicked.connect(self.task_manager.retry_all)

        self.task_manager_thread.start()
        self.event_listener.start()

        self.model = A2TaskModel(self.task_manager, self.tableView)
        self.delegate = ProgressDelegate()
        self.tableView.setItemDelegateForColumn(A2TaskModel.headers.index("Progress"), self.delegate)
        self.tableView.setModel(self.model)

        self.start_time = 0
        self.end_time = 0

    @pyqtSlot(int, int)
    def update_pbar(self, completed, total):
        self.progressBar.setRange(0, total)
        self.progressBar.setValue(completed)

    def closeEvent(self, event: QCloseEvent):
        if self.task_manager.downloading:
            ans = QMessageBox.warning(self, self.windowTitle(), "Task in progress. Exit?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ans == QMessageBox.StandardButton.No:
                event.ignore()
                return

        msg = QMessageBox()
        msg.setText("Stopping aria2...")
        msg.setWindowTitle(self.windowTitle())
        msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
        msg.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        msg.show()
        QApplication.processEvents()

        self.task_manager.stop.emit()
        self.aria2.waitForFinished()
        event.accept()

    @pyqtSlot()
    def download_modpack(self):
        if self.task_manager.downloading:
            QMessageBox.warning(self, self.windowTitle(), "Already downloading")

        newdialog = NewDownloadDialog()
        newdialog.show()
        newdialog.exec()
        if not newdialog.result():
            return
        dlinfo = newdialog.return_data
        resolver = ModpackResolver(dlinfo, Session())
        res_dialog = ForegroundTaskDialog(resolver, self)
        res_dialog.exec()
        if not res_dialog.result():
            return

        modpack_info: ModpackManifest = res_dialog.return_data
        task_list = modpack_info.modlist
        self.task_manager.start.emit(task_list)
        self.task_manager.download_complete.connect(functools.partial(self.download_complete, modpack_info))

    def export_multimc_pack(self, modpack_info: ModpackManifest):
        dialog = ForegroundTaskDialog(MultiMCPackExporter(modpack_info), parent=self)
        dialog.exec()

    def download_complete(self, modpack: ModpackManifest):
        msg = ""
        for key, value in modpack.dict(exclude={"modlist"}, exclude_defaults=True).items():
            msg += f"{key}: {value}\n"

        dialog = QDialog(self)
        dialog.setWindowTitle("Download complete")
        text_edit = QTextEdit(dialog)
        text_edit.setReadOnly(True)
        text_edit.setText(msg)
        layout = QHBoxLayout()
        layout.addWidget(text_edit)
        dialog.setLayout(layout)
        dialog.exec()
        self.task_manager.download_complete.disconnect()
