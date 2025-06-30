import os.path
import pathlib
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

from PyQt6.QtCore import QDir
from PyQt6.QtWidgets import QDialog, QMessageBox, QFileDialog

from .ui.ui_download_options_dialog import Ui_DownloadOptionsDialog


class ModpackType(IntEnum):
    CF_LOCAL = 0
    CF_ONLINE = 1
    FTB = 2


@dataclass
class InputOptions:
    modpack_type: ModpackType
    save_dir: str
    local_modpack_file: str = ""
    modpack_id: int = 0
    version_id: int = 0
    multimc: bool = False


class NewDownloadDialog(QDialog, Ui_DownloadOptionsDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.buttonGroup.setId(self.radioButton_cf_local, ModpackType.CF_LOCAL)
        self.buttonGroup.setId(self.radioButton_cf_online, ModpackType.CF_ONLINE)
        self.buttonGroup.setId(self.radioButton_ftb, ModpackType.FTB)

        self.buttonBox.accepted.connect(self.check_input)
        self.toolButton_browse_file.clicked.connect(self.browse_modpack)
        self.toolButton_browse_save_dir.clicked.connect(self.browse_save_dir)

        self.return_data: Optional[InputOptions] = None

    def browse_modpack(self):
        path = QFileDialog.getOpenFileName(self, self.windowTitle(), str(pathlib.Path.home()),
                                           filter="Curseforge Modpack (*.zip)")[0]
        self.lineEdit_modpack_file.setText(QDir.toNativeSeparators(path))

    def browse_save_dir(self):
        save_dir = QFileDialog.getExistingDirectory(self, self.windowTitle(), str(pathlib.Path.home()))
        self.lineEdit_save_dir.setText(QDir.toNativeSeparators(save_dir))

    def check_input(self):
        export_as_mmc = self.checkBox_multimc.isChecked()

        save_dir = self.lineEdit_save_dir.text().strip()
        if not os.path.isdir(save_dir):
            QMessageBox.critical(self, self.windowTitle(), "Invalid directory to save modpack")
            return

        match self.buttonGroup.checkedId():
            case ModpackType.CF_LOCAL:
                file_path = self.lineEdit_modpack_file.text().strip()
                if not os.path.isfile(file_path):
                    QMessageBox.critical(self, self.windowTitle(), "Invalid modpack file path")
                    return
                self.return_data = InputOptions(modpack_type=ModpackType.CF_LOCAL, save_dir=save_dir,
                                                multimc=export_as_mmc, local_modpack_file=file_path)

            case ModpackType.CF_ONLINE:
                QMessageBox.critical(self, self.windowTitle(), "Not implemented")
                return
            case ModpackType.FTB:
                self.return_data = InputOptions(modpack_type=ModpackType.FTB,
                                                modpack_id=self.spinBox_pack_id.value(),
                                                version_id=self.spinBox_version_id.value(),
                                                save_dir=save_dir, multimc=export_as_mmc)
        self.accept()
