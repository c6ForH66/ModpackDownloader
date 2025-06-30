from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSlot
from PyQt6.QtWidgets import QTableView

from modpack_downloader.utils.download_manager import DownloadManager
from .utils.sizes import format_size


class A2TaskModel(QAbstractTableModel):
    headers = ("File Name", "Size", "Download Speed", "Progress", "Status", "Error Message")

    def __init__(self, task_manager: DownloadManager, table: QTableView, *args):
        super().__init__(*args)
        self.table = table
        self.task_manager = task_manager
        self.task_manager.task_updated.connect(self.update_data)
        self.task_num = 0

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return self.task_num

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return len(self.headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
        return super().headerData(section, orientation, role)

    def data(self, index: QModelIndex, role: int = ...):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            task = self.task_manager.task_list[index.row()]
            match self.headers[index.column()]:
                case "File Name":
                    return task.name
                case "Size":
                    return f"{format_size(task.completedLength)}/{format_size(task.totalLength)}"
                case "Download Speed":
                    return f"{format_size(task.downloadSpeed)}/s"
                case "Progress":
                    return task.progress
                case "Status":
                    return task.status
                case "Error Message":
                    return task.errorMessage
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            header_label = self.headers[index.column()]
            if header_label == "File Name" or header_label == "Error Message":
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignCenter

        return None

    @pyqtSlot()
    def update_data(self):
        new_task_num = len(self.task_manager.task_list)
        if self.task_num != new_task_num:
            self.task_num = new_task_num
            self.layoutChanged.emit()

        # only update visible rows
        top_row = self.table.indexAt(self.table.rect().topLeft())
        bottom_row = self.table.indexAt(self.table.rect().bottomRight())
        self.dataChanged.emit(top_row, bottom_row)
