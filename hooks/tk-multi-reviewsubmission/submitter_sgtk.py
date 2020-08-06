# SSE: Modified to encompass the outside-vendor-provided
# tk-maya-playblast app functionailty, which we had also customized to fit
# our requirements (DW 2020-08-05)

import sgtk
from sgtk.platform.qt import QtCore
from sgtk.platform.qt import QtGui

import os

HookBaseClass = sgtk.get_hook_baseclass()

INITIAL_PB_STATUS = 'arev'
TIME_STR_FMT = '%Y-%m-%d (%A) %H.%M %p'


class SubmitterSGTK(HookBaseClass):
    """
    This hook allows submitting a Version to Shotgun using Shotgun Toolkit.
    """
    def __init__(self, *args, **kwargs):
        super(SubmitterSGTK, self).__init__(*args, **kwargs)

        self.__app = self.parent

        self._upload_to_shotgun = self.__app.get_setting('upload_to_shotgun')
        self._store_on_disk = self.__app.get_setting('store_on_disk')

    def can_submit(self):
        """
        Checks if it's possible to submit versions given the current
        context/environment.

        :returns:   Flag telling if the hook can submit a version.
        :rtype:     bool
        """

        msg = 'Application is not configured to store images on disk or '
        msg += 'upload to shotgun!'
        if not self._upload_to_shotgun and not self._store_on_disk:
            QtGui.QMessageBox(
                QtGui.QMessageBox.Warning,
                'Cannot submit to Shotgun',
                msg,
                flags=QtCore.Qt.Dialog
                | QtCore.Qt.MSWindowsFixedSizeDialogHint
                | QtCore.Qt.WindowStaysOnTopHint
                | QtCore.Qt.X11BypassWindowManagerHint,
            ).exec_()

            return False

        return True

    def submit_version(
        self,
        path_to_frames,
        path_to_movie,
        thumbnail_path,
        sg_publishes,
        sg_task,
        description,
        first_frame,
        last_frame,
    ):
        """
        Create a version in Shotgun for a given path and linked to the
        specified publishes.

        :param str path_to_frames: Path to the frames.
        :param str path_to_movie: Path to the movie.
        :param str thumbnail_path: Path to the thumbnail representing the
            version.
        :param list(dict) sg_publishes: Published files that have to be linked
            to the version.
        :param dict sg_task: Task that have to be linked to the version.
        :param str description: Description of the version.
        :param int first_frame: Version first frame.
        :param int last_frame: Version last frame.

        :returns:   The Version Shotgun entity dictionary that was created.
        :rtype:     dict
        """
        # get current shotgun user
        current_user = sgtk.util.get_current_user(self.__app.sgtk)

        # create a name for the version based on the file name
        # grab the file name, strip off extension, do some replacements,
        # and capitalize
        name = os.path.splitext(os.path.basename(path_to_movie))[0]
        name = name.replace('_', ' ')
        name = name.capitalize()

        # Create the version in Shotgun
        ctx = self.__app.context

        # data defaults
        data = {}
        data['code'] = name
        data['sg_status_list'] = self.__app.get_setting('new_version_status')
        data['entity'] = ctx.entity
        data['sg_task'] = sg_task
        data['sg_first_frame'] = first_frame
        data['sg_last_frame'] = last_frame
        data['sg_frames_have_slate'] = False
        data['created_by'] = current_user
        data['user'] = current_user
        data['description'] = description
        data['sg_path_to_frames'] = path_to_frames
        data['sg_movie_has_slate'] = True
        data['project'] = ctx.project

        if first_frame and last_frame:
            data['frame_count'] = last_frame - first_frame + 1
            data['frame_range'] = '{0}-{1}'.format(first_frame, last_frame)

        _ft = 'PublishedFile'
        if sgtk.util.get_published_file_entity_type(self.__app.sgtk) == _ft:
            data['published_files'] = sg_publishes
        else:
            # for type 'TankPublishedFile'
            len_pub = len(sg_publishes)
            if len_pub > 0:
                if len_pub > 1:
                    msg = '>> Only the first publish of {} '.format(len_pub)
                    msg += 'can be registered for the new version!'
                    self.__app.log_warning(msg)
                data['tank_published_file'] = sg_publishes[0]

        if self._store_on_disk:
            data['sg_path_to_movie'] = path_to_movie

        # SSE: Check if we're in a tk-maya engine, act accordingly
        # (DW 2020-08-05)
        current_engine = sgtk.platform.current_engine()
        if current_engine.name == 'tk-maya':
            data['sg_movie_has_slate'] = False
            data['sg_status_list'] = INITIAL_PB_STATUS

            if not description:
                description = ''

            n_data = self.maya_shot_playblast_publish_data(
                path_to_movie,
                description
            )
            if n_data:
                data['code'] = n_data['code']
                data['description'] = n_data['desc']
                data['sg_path_to_movie'] = n_data['path']

            # playblast submit dialog in maya
            try:
                self.playblast_submit_dialog()
                m = '>> playblast_submit_dialog > {}'.format(self.dialog)
                self.logger.info(m)
            except Exception as e:
                m = '>> playblast_submit_dialog failed > {}'.format(str(e))
                self.logger.info(m)

        # TEMP COMMENTED OUT (works fine, just don't want to keep
        # making new versions while testing other stuff)...
        # sg_version = self.__app.sgtk.shotgun.create('Version', data)
        # msg = '>> Created version in shotgun > {}'.format(str(data))
        # msg += '\n>> sg_version > {}'.format(sg_version)
        # # self.__app.log_debug(msg)
        # self.logger.info(msg)

        # # upload files:
        # self._upload_files(sg_version, path_to_movie, thumbnail_path)

        # # Remove from filesystem if required
        # if not self._store_on_disk and os.path.exists(path_to_movie):
        #     os.unlink(path_to_movie)

        # return sg_version
        # TEMP COMMENTED OUT ^^^

    def _upload_files(self, sg_version, output_path, thumbnail_path):
        """
        Upload the required files to Shotgun.

        :param dict sg_version:     Version to which uploaded files should be
            linked.
        :param str output_path:     Media to upload to Shotgun.
        :param str thumbnail_path:  Thumbnail to upload to Shotgun.
        """
        # Upload in a new thread and make our own event loop to wait for the
        # thread to finish.
        event_loop = QtCore.QEventLoop()
        thread = UploaderThread(
            self.__app,
            sg_version,
            output_path,
            thumbnail_path,
            self._upload_to_shotgun
        )
        thread.finished.connect(event_loop.quit)
        thread.start()
        event_loop.exec_()

        # log any errors generated in the thread
        for e in thread.get_errors():
            self.__app.log_error(e)

    def maya_shot_playblast_version(self):
        self.logger.info('>> maya_shot_playblast_version')

    def maya_shot_playblast_publish_data(self, o_path, o_desc):
        """Modify some of the playblast media publish value prior to publish
        for SSE requirements.

        Args:
            o_path (str): the original path to the media (local)
            o_desc (str): the original decription from the artist ('' if none)

        Returns:
            dict: key/value pairs of modified data.
        """
        import maya.cmds as cmds
        from datetime import datetime

        new_data = {}

        # 'code' modification for version add
        new_code = os.path.basename(o_path)
        new_data['code'] = new_code

        # 'description' modification for datetime add
        current_time = datetime.now().strftime(TIME_STR_FMT)
        new_desc = '{0}\n{1}'.format(o_desc, current_time)
        new_data['desc'] = new_desc

        # 'path' modification for template output fields add
        scene_name = cmds.file(q=True, sn=True)
        wk_template = self.__app.sgtk.templates.get('maya_shot_work')
        pb_template = self.__app.sgtk.templates.get('maya_shot_playblast')
        wk_fields = wk_template.get_fields(scene_name)
        new_data['path'] = pb_template.apply_fields(wk_fields)

        self.logger.info('>> new_data > {}'.format(new_data))

        return new_data

    def playblast_submit_dialog(self):
        # main dialog
        self.dialog = QtGui.QDialog()
        self.dialog.setObjectName('PlayblastDialog')
        self.dialog.resize(440, 240)
        self.dialog.setMinimumSize(QtCore.QSize(440, 240))
        self.dialog.setMaximumSize(QtCore.QSize(440, 240))

        self.dialog.setWindowFlags(
            self.dialog.windowFlags() | QtCore.Qt.WindowStaysOnTopHint
        )

        self.dialog.setWindowTitle(
            QtGui.QApplication.translate(
                "PlayblastDialog",
                "Playblast to Shotgun",
                None,
                QtGui.QApplication.UnicodeUTF8
            )
        )

        # main layout & grid
        self.dialog.gridLayoutWidget = QtGui.QWidget(self.dialog)
        self.dialog.gridLayoutWidget.setGeometry(QtCore.QRect(9, 9, 421, 221))
        self.dialog.gridLayoutWidget.setObjectName('gridLayoutWidget')

        self.dialog.gridLayout_main = QtGui.QGridLayout(
            self.dialog.gridLayoutWidget
        )

        self.dialog.gridLayout_main.setContentsMargins(0, 0, 0, 0)
        self.dialog.gridLayout_main.setObjectName('gridLayout_main')

        # upload button
        self.dialog.pushButton_upload = QtGui.QPushButton(
            self.dialog.gridLayoutWidget
        )
        self.dialog.pushButton_upload.setObjectName('pushButton_upload')

        self.dialog.gridLayout_main.addWidget(
            self.dialog.pushButton_upload,
            2,
            0,
            1,
            1
        )

        # comments groupbox
        self.dialog.groupBox_comments = QtGui.QGroupBox(
            self.dialog.gridLayoutWidget
        )

        self.dialog.groupBox_comments.setAlignment(QtCore.Qt.AlignCenter)
        self.dialog.groupBox_comments.setFlat(False)
        self.dialog.groupBox_comments.setObjectName('groupBox_comments')

        self.dialog.groupBox_comments.setTitle(
            QtGui.QApplication.translate(
                "PlayblastDialog",
                "Artist Comments",
                None,
                QtGui.QApplication.UnicodeUTF8
            )
        )

        # comments textedit
        self.dialog.textEdit = QtGui.QTextEdit(self.dialog.groupBox_comments)
        self.dialog.textEdit.setGeometry(QtCore.QRect(12, 20, 395, 131))
        self.dialog.textEdit.setMinimumSize(QtCore.QSize(395, 131))
        self.dialog.textEdit.setMaximumSize(QtCore.QSize(395, 131))
        self.dialog.textEdit.setObjectName('textEdit_comments')

        self.dialog.gridLayout_main.addWidget(
            self.dialog.groupBox_comments,
            1,
            0,
            1,
            1
        )

        self.dialog.pushButton_upload.setText(
            QtGui.QApplication.translate(
                "PlayblastDialog",
                "Upload as Version to Shotgun",
                None,
                QtGui.QApplication.UnicodeUTF8
            )
        )

        # signals and slots
        self.dialog.pushButton_upload.clicked.connect(
            self.maya_shot_playblast_version
        )

        # launch dialog
        self.dialog.exec_()


class UploaderThread(QtCore.QThread):
    """
    Simple worker thread that encapsulates uploading to shotgun.
    Broken out of the main loop so that the UI can remain responsive
    even though an upload is happening.
    """
    def __init__(
        self,
        app,
        version,
        path_to_movie,
        thumbnail_path,
        upload_to_shotgun
    ):
        QtCore.QThread.__init__(self)
        self._app = app
        self._version = version
        self._path_to_movie = path_to_movie
        self._thumbnail_path = thumbnail_path
        self._upload_to_shotgun = upload_to_shotgun
        self._errors = []

    def get_errors(self):
        """
        Returns the errors collected while uploading files to Shotgun.

        :returns:   List of errors
        :rtype:     [str]
        """
        return self._errors

    def run(self):
        """
        This function implements what get executed in the UploaderThread.
        """
        upload_error = False

        if self._upload_to_shotgun:
            try:
                self._app.sgtk.shotgun.upload(
                    'Version',
                    self._version['id'],
                    self._path_to_movie,
                    'sg_uploaded_movie',
                )
            except Exception as e:
                m = '>> Movie upload to Shotgun failed > {}'.format(str(e))
                self._errors.append(m)
                upload_error = True

        if not self._upload_to_shotgun or upload_error:
            try:
                self._app.sgtk.shotgun.upload_thumbnail(
                    'Version', self._version['id'], self._thumbnail_path
                )
            except Exception as e:
                m = ">> Thumbnail upload to Shotgun failed > {}".format(str(e))
                self._errors.append(m)
