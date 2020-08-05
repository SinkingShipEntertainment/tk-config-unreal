from sgtk.platform.qt import QtCore
from sgtk.platform.qt import QtGui


class PlayblastDialog(QtGui.QWidget):
    """
    Main application dialog window
    """

    # def __init__(self, app, handler, parent=None):
    def __init__(self, parent=None):
        # call the base class
        QtGui.QWidget.__init__(self, parent)

        # self._app = app
        # self._handler = handler

        # get the UI
        self.setup_ui()

        # lastly, set up our very basic UI
        # self._ui.btnPlayblast.clicked.connect(self.doPlayblast)

    def setup_ui(self):
        self.setObjectName("PlayblastDialog")
        self.resize(440, 240)
        self.setMinimumSize(QtCore.QSize(440, 240))
        self.setMaximumSize(QtCore.QSize(440, 240))

        self.gridLayoutWidget = QtGui.QWidget(self)
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

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        self.setWindowTitle(
            QtGui.QApplication.translate(
                "PlayblastDialog",
                "Playblast to Shotgun",
                None,
                QtGui.QApplication.UnicodeUTF8
            )
        )

        self.pushButton_playblast.setText(
            QtGui.QApplication.translate(
                "PlayblastDialog",
                "Playblast",
                None,
                QtGui.QApplication.UnicodeUTF8
            )
        )

        self.checkBox_upload.setText(
            QtGui.QApplication.translate(
                "PlayblastDialog",
                "Upload to Shotgun",
                None,
                QtGui.QApplication.UnicodeUTF8
            )
        )

        self.groupBox_comments.setTitle(
            QtGui.QApplication.translate(
                "PlayblastDialog",
                "Artist Comments",
                None,
                QtGui.QApplication.UnicodeUTF8
            )
        )


if __name__ == '__main__':
    pb_dialog = PlayblastDialog()
    pb_dialog.show()
