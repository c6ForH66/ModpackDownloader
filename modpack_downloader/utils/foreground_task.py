import abc
from abc import abstractmethod

import PyQt6.sip
from PyQt6.QtCore import QObject, pyqtSignal


class AbstractQObjectMeta(PyQt6.sip.wrappertype, abc.ABCMeta):
    pass


class ForegroundTask(QObject, metaclass=AbstractQObjectMeta):
    complete = pyqtSignal(object)
    progress_changed = pyqtSignal(int, int)
    failed = pyqtSignal(str)

    status = pyqtSignal(str)

    @abstractmethod
    def run(self): ...
