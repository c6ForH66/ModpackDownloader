# Form implementation generated from reading ui file 'ui\foreground_task.ui'
#
# Created by: PyQt6 UI code generator 6.5.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_ForegroundTaskDialog(object):
    def setupUi(self, ForegroundTaskDialog):
        ForegroundTaskDialog.setObjectName("ForegroundTaskDialog")
        ForegroundTaskDialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        ForegroundTaskDialog.resize(321, 80)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ForegroundTaskDialog.sizePolicy().hasHeightForWidth())
        ForegroundTaskDialog.setSizePolicy(sizePolicy)
        ForegroundTaskDialog.setMinimumSize(QtCore.QSize(300, 80))
        ForegroundTaskDialog.setModal(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(ForegroundTaskDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.progressBar = QtWidgets.QProgressBar(parent=ForegroundTaskDialog)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(parent=ForegroundTaskDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label_progress = QtWidgets.QLabel(parent=ForegroundTaskDialog)
        self.label_progress.setObjectName("label_progress")
        self.horizontalLayout.addWidget(self.label_progress)
        self.buttonBox = QtWidgets.QDialogButtonBox(parent=ForegroundTaskDialog)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(ForegroundTaskDialog)
        self.buttonBox.rejected.connect(ForegroundTaskDialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(ForegroundTaskDialog)

    def retranslateUi(self, ForegroundTaskDialog):
        _translate = QtCore.QCoreApplication.translate
        ForegroundTaskDialog.setWindowTitle(_translate("ForegroundTaskDialog", "Mod Resolver"))
        self.label.setText(_translate("ForegroundTaskDialog", "status"))
        self.label_progress.setText(_translate("ForegroundTaskDialog", "progress"))
