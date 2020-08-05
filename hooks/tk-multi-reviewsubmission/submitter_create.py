# SSE: Modified to encompass the outside-vendor-provided
# tk-maya-playblast app functionailty, which we had also customized to fit
# our requirements (DW 2020-08-04)

import os
import sgtk
from sgtk.platform.qt import QtCore
from sgtk.platform.qt import QtGui

HookBaseClass = sgtk.get_hook_baseclass()

TIME_STR_FMT = '%Y-%m-%d (%A) %H.%M %p'


class SubmitterCreate(HookBaseClass):
    """
    This hook allow to submit a Version to Shotgun using Shotgun Create.
    """

    def __init__(self, *args, **kwargs):
        super(SubmitterCreate, self).__init__(*args, **kwargs)

        self.__app = self.parent

        desktopclient_framework = self.load_framework(
            'tk-framework-desktopclient_v0.x.x'
        )
        self.__create_client_module = desktopclient_framework.import_module(
            'create_client'
        )

    def can_submit(self):
        """
        Checks if it's possible to submit versions given the current
        context/environment.

        :returns:               Flag telling if the hook can submit a version.
        :rtype:                 bool
        """

        if not self.__create_client_module.is_create_installed():

            QtGui.QMessageBox(
                QtGui.QMessageBox.Warning,
                'Cannot submit to Shotgun',
                'Shotgun Create is not installed!',
                flags=QtCore.Qt.Dialog
                | QtCore.Qt.MSWindowsFixedSizeDialogHint
                | QtCore.Qt.WindowStaysOnTopHint
                | QtCore.Qt.X11BypassWindowManagerHint,
            ).exec_()

            self.__create_client_module.open_shotgun_create_download_page(
                self.__app.sgtk.shotgun
            )

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
            version. (Unused)
        :param list(dict) sg_publishes: Published files that have to be linked
            to the version.
        :param dict sg_task: Task that have to be linked to the version.
        :param str description: Description of the version.
        :param int first_frame: Version first frame (Unused)
        :param int last_frame: Version last frame (Unused)

        NOTE: Shotgun Create will create the thumbnail for the movie passed in
        and will inspect the media to get the first and last frame, so these
        parameters are ignored.

        :returns: The Version Shotgun entity dictionary that was created.
        :rtype:   dict

        Because of the asynchronous nature of this hook. It doesn't return any
        Version Shotgun entity dictionary.
        """

        path_to_media = path_to_movie or path_to_frames

        # Starts Shotgun Create in the right context if not already running.
        ok = self.__create_client_module.ensure_create_server_is_running(
            self.__app.sgtk.shotgun
        )

        if not ok:
            raise RuntimeError('Unable to connect to Shotgun Create.')

        client = self.__create_client_module.CreateClient(
            self.__app.sgtk.shotgun
        )

        if not sg_task:
            sg_task = self.__app.context.task

        vers_draft_args = dict()
        vers_draft_args['task_id'] = sg_task['id']
        vers_draft_args['path'] = path_to_media
        vers_draft_args['version_data'] = dict()

        if sg_publishes:
            vers_draft_args['version_data']['published_files'] = sg_publishes

        if description:
            vers_draft_args['version_data']['description'] = description

        # SSE: Check that we're in a tk-maya engine, then modify values
        # accordingly (DW 2020-08-04)
        # current_engine = sgtk.platform.current_engine()
        # if current_engine.name == 'tk-maya':
        #     if not description:
        #         description = ''

        #     n_data = self.maya_shot_playblast_publish_data(
        #         path_to_media,
        #         description
        #     )
        #     if n_data:
        #         vers_draft_args['version_data']['code'] = n_data['code']
        #         vers_draft_args['version_data']['description'] = n_data['desc']
        #         vers_draft_args['path'] = n_data['path']

        client.call_server_method('sgc_open_version_draft', vers_draft_args)

        # Because of the asynchronous nature of this hook. It doesn't return
        # any Version Shotgun entity dictionary.
        return None

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
# --- eof
