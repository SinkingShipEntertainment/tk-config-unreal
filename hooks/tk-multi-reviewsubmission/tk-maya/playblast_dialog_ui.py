# -*- coding: utf-8 -*-

# PlayblastDialog implementation generated from reading ui file
# 'playblast_dialog.ui'
#
# Created: Wed Aug 05 13:00:36 2020
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui


class Ui_PlayblastDialog(object):
    def setupUi(self, PlayblastDialog):
        PlayblastDialog.setObjectName("PlayblastDialog")
        PlayblastDialog.resize(440, 240)
        PlayblastDialog.setMinimumSize(QtCore.QSize(440, 240))
        PlayblastDialog.setMaximumSize(QtCore.QSize(440, 240))
        self.gridLayoutWidget = QtGui.QWidget(PlayblastDialog)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(9, 9, 421, 221))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout_main = QtGui.QGridLayout(self.gridLayoutWidget)
        self.gridLayout_main.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_main.setObjectName("gridLayout_main")
        self.pushButton_playblast = QtGui.QPushButton(self.gridLayoutWidget)
        self.pushButton_playblast.setObjectName("pushButton_playblast")
        self.gridLayout_main.addWidget(self.pushButton_playblast, 2, 0, 1, 1)
        self.checkBox_upload = QtGui.QCheckBox(self.gridLayoutWidget)
        self.checkBox_upload.setObjectName("checkBox_upload")
        self.gridLayout_main.addWidget(self.checkBox_upload, 0, 0, 1, 1)
        self.groupBox_comments = QtGui.QGroupBox(self.gridLayoutWidget)
        self.groupBox_comments.setAlignment(QtCore.Qt.AlignCenter)
        self.groupBox_comments.setFlat(False)
        self.groupBox_comments.setObjectName("groupBox_comments")
        self.textEdit = QtGui.QTextEdit(self.groupBox_comments)
        self.textEdit.setGeometry(QtCore.QRect(12, 20, 395, 131))
        self.textEdit.setMinimumSize(QtCore.QSize(395, 131))
        self.textEdit.setMaximumSize(QtCore.QSize(395, 131))
        self.textEdit.setObjectName("textEdit")
        self.gridLayout_main.addWidget(self.groupBox_comments, 1, 0, 1, 1)

        self.retranslateUi(PlayblastDialog)
        QtCore.QMetaObject.connectSlotsByName(PlayblastDialog)

    def retranslateUi(self, PlayblastDialog):
        PlayblastDialog.setWindowTitle(QtGui.QApplication.translate("PlayblastDialog", "Playblast to Shotgun", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_playblast.setText(QtGui.QApplication.translate("PlayblastDialog", "Playblast", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBox_upload.setText(QtGui.QApplication.translate("PlayblastDialog", "Upload to Shotgun", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_comments.setTitle(QtGui.QApplication.translate("PlayblastDialog", "Artist Comments", None, QtGui.QApplication.UnicodeUTF8))

