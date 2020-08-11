# SSE: Modified to replicate our legacy+ Shotgun configuration post_publish
# functionailty, which was customized to fit our requirements.
# linter: flake8
# docstring style: Google
# (DW 2020-08-11)

import os
import sgtk
import shutil

HookBaseClass = sgtk.get_hook_baseclass()

SSE_HEADER = '>> Executing Sinking Ship'


class PostPhaseHook(HookBaseClass):
    """
    This hook defines methods that are executed after each phase of a publish:
    validation, publish, and finalization. Each method receives the publish
    tree instance being used by the publisher, giving full control to further
    curate the publish tree including the publish items and the tasks attached
    to them. See the :class:`PublishTree` documentation for additional details
    on how to traverse the tree and manipulate it.
    """

    # See the developer docs for more information about the methods that can be
    # defined here: https://developer.shotgunsoftware.com/tk-multi-publish2/

    def post_publish(self, publish_tree):
        """This method is executed after the publish pass has completed for
        each item in the tree, before the finalize pass.

        A :ref:`publish-api-tree` instance representing the items that were
        published is supplied as an argument. The tree can be traversed in this
        method to inspect the items and process them collectively.

        To glean information about the publish state of particular items, you
        can iterate over the items in the tree and introspect their
            :py:attr:`~.api.PublishItem.properties` dictionary.
        This requires customizing your publish plugins to populate any specific
        publish information that you want to process collectively here.

        NOTE: You will not be able to use the item's
            :py:attr:`~.api.PublishItem.local_properties` in this hook since
            :py:attr:`~.api.PublishItem.local_properties` are only accessible
        during the execution of a publish plugin.

        Args:
            publish_tree (obj): The :ref:`publish-api-tree` instance
                representing the items to be published.
        """
        m = '{} post_publish'.format(SSE_HEADER)
        self.logger.debug(m)

        ctx = self.__app.context

        # engine
        current_engine = sgtk.platform.current_engine()
        if current_engine.name == 'tk-aftereffects':
            pass
        if current_engine.name == 'tk-houdini':
            pass
        if current_engine.name == 'tk-mari':
            pass
        if current_engine.name == 'tk-maya':
            self.post_publish_maya(ctx)
        if current_engine.name == 'tk-nuke':
            pass

    def post_publish_maya(self, ctx):
        """Calls the appropriate method to run after a publish depending on
        the Pipeline Step in a session running the Maya engine.

        Args:
            ctx (obj): A Shotgun Context instance for the DCC session provided
                by the Shotgun Toolkit of the current Project.
        """
        m = '{} post_publish_maya'.format(SSE_HEADER)
        self.logger.debug(m)

        import maya.cmds as cmds
        scene_name = cmds.file(q=True, sn=True)

        e_type = ctx.entity['type']
        p_step = ctx.step['name']

        wk_template = self.__app.sgtk.templates.get('maya_shot_work')
        wk_fields = wk_template.get_fields(scene_name)

        # method calls based on Shotgun pipeline steps as defined at SSE
        # NOTE: pipeline steps that call no method are included for possible
        # future use
        if e_type == 'Asset':
            # pipeline steps for Asset, in order
            if p_step == 'Modeling':
                pass
            if p_step == 'Rigging':
                pass
            if p_step == 'Texturing':
                pass
            if p_step == 'Surfacing':
                pass
            if p_step == 'FX':
                pass

        if e_type == 'Shot':
            # pipeline steps - Shot, in order
            if p_step == 'Tracking & Layout':
                self.post_publish_maya_tlo(scene_name, wk_fields)
            if p_step == 'Animation':
                pass
            if p_step == 'Character Finaling':
                pass
            if p_step == 'FX':
                pass
            if p_step == 'Lighting':
                pass

    def post_publish_maya_tlo(self, scene_name, wk_fields):
        """Copies the TLO file to a matching ANIM file, in the current Shotgun
        user's work directory for the destination Pipeline Step.
        NOTE: we could potentially have it Publish the ANIM file (an 'initial
        anim file'), but for the short term we'll just mimic the legacy+
        behaviour of a simple file copy.

        Args:
            scene_name (str): The full path to the curently open Maya file.
            wk_fields (dict): Fields provided by the Shotgun Toolkit template
                for the Project.
        """
        m = '{} post_publish_maya_tlo'.format(SSE_HEADER)
        self.logger.debug(m)

        # get current shotgun user
        current_user = sgtk.util.get_current_user(self.__app.sgtk)

        # data for the target ANIM Shot
        shot_data = {}
        shot_data['Step'] = u'ANIM'
        shot_data['Sequence'] = wk_fields['Sequence']
        shot_data['Shot'] = wk_fields['Shot']
        shot_data['current_user_name'] = current_user
        shot_data['version'] = 1

        wk_template = self.__app.sgtk.templates.get('maya_shot_work')
        anim_file = wk_template.apply_fields(shot_data)
        anim_file_dir = os.path.dirname(anim_file)

        # make the destination ANIM user work directory
        if not os.path.exists(anim_file_dir):
            os.makedirs(anim_file_dir)

        # copy!
        self._copy_file(scene_name, anim_file)

    def _copy_file(self, src, dst):
        """Copy a source file to a destination file.

        Args:
            src (str): The full source filepath.
            dst (str): The full destination filepath.
        """
        try:
            shutil.copy2(src, dst)
            m = '{0} copied file {1} -> {2}'.format(SSE_HEADER, src, dst)
            self.logger.debug(m)
        except Exception as e:
            m = '{0} file copy failed {1} > {2}'.format(
                SSE_HEADER,
                dst,
                str(e)
            )
            self.logger.debug(m)
# --- eof
