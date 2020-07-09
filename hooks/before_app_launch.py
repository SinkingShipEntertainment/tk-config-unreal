# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Before App Launch Hook

This hook is executed prior to application launch and is useful if you need
to set environment variables or run scripts as part of the app initialization.
"""

import os
import sys
import tank

# --- get Shotgun Desktop Console logging going...
import sgtk
logger = sgtk.platform.get_logger(__name__)
my_sep = ('=' * 10)

class BeforeAppLaunch(tank.Hook):
    """
    Hook to set up the system prior to app launch.
    """

    def execute(self, app_path, app_args, version, engine_name, **kwargs):
        """
        The execute functon of the hook will be called prior to starting the required application

        :param app_path: (str) The path of the application executable
        :param app_args: (str) Any arguments the application may require
        :param version: (str) version of the application being run if set in the
            "versions" settings of the Launcher instance, otherwise None
        :param engine_name (str) The name of the engine associated with the
            software about to be launched.

        """
        # accessing the current context (current shot, etc)
        # can be done via the parent object
        #
        # > multi_launchapp = self.parent
        # > current_entity = multi_launchapp.context.entity
        #
        # you can set environment variables like this:
        # os.environ["MY_SETTING"] = "foo bar"

        # Log args
        logger.debug('app_path    > {}'.format(app_path))
        logger.debug('app_args    > {}'.format(app_args))
        logger.debug('version     > {}'.format(version))
        logger.debug('engine_name > {}'.format(engine_name))
        logger.debug('kwargs      > {}'.format(kwargs))

        os.environ["XBMLANGPATH"] = "X:\\tools\\release\\icons"

        # --- SG supplied ENVIRONMENT VARIABLES...
        os.environ['SG_APP_VERSION'] = '{}'.format(version)

        multi_launchapp = self.parent
        os.environ['SG_CURR_ENTITY'] = '{}'.format(multi_launchapp.context.entity)
        os.environ['SG_CURR_STEP'] = '{}'.format(multi_launchapp.context.step)
        os.environ['SG_CURR_TASK'] = '{}'.format(multi_launchapp.context.task)
        os.environ['SG_CURR_PROJECT'] = '{}'.format(multi_launchapp.context.project)
        os.environ['SG_CURR_LOCATIONS'] = '{}'.format(multi_launchapp.context.filesystem_locations)

        # --- get the correct studio tools in the paths (SYS & PYTHONPATH)...
        os.environ['CURR_PROJECT'] = '{}'.format(multi_launchapp.context.project['name'])
        project_name = os.environ['CURR_PROJECT']

        # --- Set instance variables...
        self._version = version
        self._engine_name = engine_name

        # --- Unified studio tools pathing!
        self._repo_path = self._return_repo_path(project_name)

        # --- Make the SSE Shotgun API available...
        self._sg_a3_path = '{}/shotgun/api3'.format(self._repo_path)

        # --- Call methods based on the Toolkit engine we're invoking
        # --- (e.g. Maya > 'tk-maya', Nuke > 'tk-nuke', etc.)...
        if engine_name == 'tk-maya':
            self._tk_maya_env_setup()

        if engine_name == 'tk-nuke':
            self._tk_nuke_env_setup()

        if engine_name == 'tk-aftereffects':
            self._tk_aftereffects_env_setup()

        if engine_name == 'tk-houdini':
            self._tk_houdini_env_setup()

        if engine_name == 'tk-natron':
            self._tk_natron_env_setup()

    def _return_repo_path(self, project_name):
        """
        Use Shotgun (Toolkit and Database) to get data
        and return the correct code repo root path for
        the Project that Toolkit launched.
        @return str repo_path: The root of the path
                               based on information
                               gleaned from Shotgun.
        """
        repo_path = None

        logger.debug(my_sep)

        shotgun_inst = sgtk.api.shotgun.connection.get_sg_connection()
        sg_filters = [['project.Project.name', 'is', project_name]]
        sg_fields = ['id', 'code', 'project', 'sg_ss_tools_repo', 'windows_path']
        sgtk_configs = shotgun_inst.find('PipelineConfiguration', sg_filters, sg_fields)

        wanted_repo_key = None

        sg_auth = sgtk.get_authenticated_user()
        sgtk_core_user = sg_auth.login

        sgtk_module_path = sgtk.get_sgtk_module_path()
        if '\\' in sgtk_module_path:
            sgtk_module_path = sgtk_module_path.replace('\\', '/')
        sgtk_cfg_path = '/'.join(sgtk_module_path.split('/')[:5])
        logger.debug('sgtk_module_path >> {}'.format(sgtk_module_path))
        logger.debug('sgtk_cfg_path >> {}'.format(sgtk_cfg_path))

        for my_config in sgtk_configs:
            my_config_repo_key = my_config['sg_ss_tools_repo']
            my_config_path = my_config['windows_path']
            if '\\' in my_config_path:
                my_config_path = my_config_path.replace('\\', '/')
                if my_config_path == sgtk_cfg_path:
                    wanted_repo_key = my_config_repo_key
                    logger.debug('wanted_repo_key >> {}'.format(wanted_repo_key))
                    break

        if wanted_repo_key:
            if wanted_repo_key == 'dev':
                repo_path = 'X:/dev/ss_dev_{0}/{1}_repo'.format(sgtk_core_user, project_name)
                # --- If it's not a Project-specific repo, we have to resort to
                # --- the generic studio repo...
                if not os.path.exists(repo_path):
                    repo_path = 'X:/dev/ss_dev_{0}/ss_studio_repo'.format(sgtk_core_user, project_name)
            elif wanted_repo_key == 'project':
                repo_path = 'X:/tools/projects/{0}/{0}_repo'.format(project_name)
            else:
                repo_path = 'X:/tools/ss_studio_repo'
        logger.debug(my_sep)

        return repo_path

    def _tk_maya_env_setup(self):
        """
        Method to set up all the wanted environment
        variables when launching a Maya session.
        """
        _setup = '_tk_maya_env_setup'
        self._headers(_setup)

        maya_script_paths = []
        maya_script_paths.append('{}/maya/scripts/mel'.format(self._repo_path))
        maya_script_paths.append('{}/maya/scripts/vtool'.format(self._repo_path))
        maya_script_paths.append('{}/maya/scripts/mel/anim'.format(self._repo_path))
        maya_script_paths.append('{}/maya/scripts/mel/light'.format(self._repo_path))
        maya_script_paths.append('{}/maya/scripts/mel/modeling'.format(self._repo_path))
        maya_script_paths.append('{}/maya/scripts/mel/rigging'.format(self._repo_path))
        os.environ['MAYA_SCRIPT_PATH'] = ';'.join(maya_script_paths)

        maya_tool_path = '{}/maya/scripts'.format(self._repo_path)
        module_path = '{}/maya/modules'.format(self._repo_path)
        plugin_path = '{}/maya/plug-ins'.format(self._repo_path)

        script_paths = []
        script_paths.append(self._sg_a3_path)
        script_paths.append(maya_tool_path)
        for script_path in script_paths:
            sys.path.insert(0, script_path)

        for script_path in script_paths:
            old_py_path = os.environ['PYTHONPATH']
            if script_path in old_py_path:
                logger.debug('Found {} in PYTHONPATH, no need to add it.'.format(script_path))
            else:
                logger.debug('old_py_path > {}'.format(old_py_path))
                old_py_path_bits = old_py_path.split(';')

                old_py_path_bits.insert(0, script_path)
                new_py_path = ';'.join(old_py_path_bits)

                logger.debug('new_py_path > {}'.format(new_py_path))
                os.environ['PYTHONPATH'] = new_py_path

        import python
        reload (python)

        # --- specific related to Maya versions...
        module_path = '{0}{1}{2}'.format(module_path, os.sep, self._version)
        logger.debug('module_path > {}'.format(module_path))

        if self._version in ['2018', '2020']:
            # --- General plugins...
            os.environ['MAYA_PLUG_IN_PATH'] = '{0}{1}{2}'.format(plugin_path, os.sep, self._version)

            # --- VRay (legacy, we don't actually use it,
            # --- but maybe for retrieving old Assets?)...
            vray_home = 'C:{0}Program Files{0}Autodesk{0}Maya{1}{0}vray'.format(os.sep, self._version)
            v_main_key = 'VRAY_FOR_MAYA{}_MAIN_x64'.format(self._version)
            os.environ[v_main_key] = vray_home
            v_plug_key =  'VRAY_FOR_MAYA{}_PLUGINS_x64'.format(self._version)
            os.environ[v_plug_key] = '{0}{1}{2}'.format(vray_home, os.sep, 'vrayplugins')

            vray_chaos_root = 'C:{0}Program Files{0}Chaos Group{0}V-Ray{0}Maya {1} for x64'.format(os.sep, self._version)
            v_tools_key = 'VRAY_TOOLS_MAYA{}_x64'.format(self._version)
            os.environ[v_tools_key] = '{0}{1}bin'.format(vray_chaos_root, os.sep)
            v_osl_key = 'VRAY_OSL_PATH_MAYA{}_x64'.format(self._version)
            os.environ[v_osl_key] = '{0}{1}opensl'.format(vray_chaos_root, os.sep)

            # --- Yeti...
            # yeti_vers = 'v3.1.10'
            # if self._version == '2020':
            #     yeti_vers = 'v3.6.2'

            yeti_vers = 'v3.6.2'

            yeti_home = '{1}{0}yeti{0}{2}'.format(os.sep, module_path, yeti_vers)
            logger.debug('yeti_home > {}'.format(yeti_home))

            os.environ['YETI_HOME'] = yeti_home
            os.environ['PATH'] = '{0}{1}{2}{3}bin'.format(os.environ['PATH'], os.pathsep, yeti_home, os.sep)
            os.environ['XBMLANGPATH'] = '{0}{1}{2}{3}icons'.format(os.environ['XBMLANGPATH'], os.pathsep, yeti_home, os.sep)
            os.environ['MAYA_PLUG_IN_PATH'] = '{0}{1}{2}{3}plug-ins'.format(os.environ['MAYA_PLUG_IN_PATH'], os.pathsep, yeti_home, os.sep)
            os.environ['MAYA_SCRIPT_PATH'] = '{0}{1}{2}{3}scripts'.format(os.environ['MAYA_SCRIPT_PATH'], os.pathsep, yeti_home, os.sep)

            if 'VRAY_PLUGINS_x64' in os.environ.keys():
                os.environ['VRAY_PLUGINS_x64'] = '{0}{1}{2}{3}bin'.format(os.environ['VRAY_PLUGINS_x64'], os.pathsep, yeti_home, os.sep)
            else:
                os.environ['VRAY_PLUGINS_x64'] = '{0}{1}bin'.format(yeti_home, os.sep)

            # --- Needed to get the module path in, as earlier just defines the
            # --- local Vray install path initially (DW 2020-07-09)
            if v_plug_key in os.environ.keys():
                os.environ[v_plug_key] = '{0}{1}{2}{3}bin'.format(
                    os.environ[v_plug_key],
                    os.pathsep,
                    yeti_home,
                    os.sep
                )
            else:
                os.environ[v_plug_key] = '{0}{1}bin'.format(yeti_home, os.sep)
            # --- ^^^

            os.environ['ARNOLD_PLUGIN_PATH'] = '{0}{1}{2}{3}bin'.format(
                os.environ['ARNOLD_PLUGIN_PATH'],
                os.pathsep,
                yeti_home,
                os.sep
            )

            os.environ['MTOA_EXTENSIONS_PATH'] = '{0}{1}{2}{3}plug-ins'.format(
                os.environ["MTOA_EXTENSIONS_PATH"],
                os.pathsep,
                yeti_home,
                os.sep
            )

            # --- Module path wrap-up (additions should be placed in
            # --- the 'add_modules' *NOT* 'main_module_list')...
            main_module_list = [
                module_path,
                yeti_home
            ]

            add_modules = [
                'brSmoothWeights',
                'iDeform',
                'AtomsMaya',
                'ziva'
            ]

            for add_module in add_modules:
                _home = '{0}{1}{2}'.format(module_path, os.sep, add_module)
                main_module_list.append(_home)
                logger.debug('Added Maya module > {}'.format(_home))

            maya_module_path = (os.pathsep).join(main_module_list)
            logger.debug('maya_module_path > {}'.format(maya_module_path))

            os.environ['MAYA_MODULE_PATH'] = maya_module_path

            # --- Legacy vtool stuff, need to revisit/update/remove possibly...
            vtool_legacy_path = 'X:\\tools\\sinking_ship\\maya\\scripts\\vtool'
            os.environ['PATH'] = '{0}{1}{2}'.format(os.environ['PATH'], os.pathsep, vtool_legacy_path)

            # --- Redshift (legacy, we don't actually use it,
            # --- but maybe for retrieving old Assets?)...
            os.environ["REDSHIFT_COREDATAPATH"] =  "C:\\ProgramData\\Redshift"
            os.environ["REDSHIFT_PLUG_IN_PATH"] = "C:\\ProgramData\\Redshift\\Plugins\\Maya\\{}\\nt-x86-64".format(self._version)
            os.environ["REDSHIFT_SCRIPT_PATH"] =  "C:\\ProgramData\\Redshift\\Plugins\\Maya\\Common\\scripts"
            os.environ["REDSHIFT_XBMLANGPATH"] =  "C:\\ProgramData\\Redshift\\Plugins\\Maya\\Common\\icons"
            os.environ["REDSHIFT_RENDER_DESC_PATH"] =  "C:\\ProgramData\\Redshift\\Plugins\\Maya\\Common\\rendererDesc"
            os.environ["REDSHIFT_CUSTOM_TEMPLATE_PATH"] =  "C:\\ProgramData\\Redshift\\Plugins\\Maya\\Common\\scripts\\NETemplate"
            os.environ["REDSHIFT_MAYAEXTENSIONSPATH"] =  "C:\\ProgramData\\Redshift\\Plugins\\Maya\\{}\\nt-x86-64\\extensions".format(self._version)
            os.environ["REDSHIFT_PROCEDURALSPATH"] =  "C:\\ProgramData\\Redshift\\Procedural"

        else:
            logger.debug('No Maya product/version specific environment variables required.')

        # --- Tell the user what's up...
        self.env_paths_sanity_check()

    def _tk_nuke_env_setup(self):
        """
        Method to set up all the wanted environment
        variables when launching a Nuke session.
        """
        _setup = '_tk_nuke_env_setup'
        self._headers(_setup)

        script_paths = []
        script_paths.append(self._sg_a3_path)
        for script_path in script_paths:
            sys.path.insert(0, script_path)

        # Check if NUKE_PATH exists.
        # TODO - After NUKE_PATH is purged from boxes, remove condition so we find out-of-sync boxes
        nuke_plugin_path = '{}/nuke'.format(self._repo_path).replace('/', '\\')
        if 'NUKE_PATH' in os.environ:
            logger.debug('Found existing NUKE_PATH in os.environ...')
            os.environ['NUKE_PATH'] = os.pathsep.join([nuke_plugin_path, os.environ['NUKE_PATH']])
        else:
            logger.debug('No existing NUKE_PATH in os.environ, creating...')
            os.environ['NUKE_PATH'] = '{}'.format(nuke_plugin_path)
        #os.environ['NUKE_PATH'] = os.pathsep.join([nuke_plugin_path, os.environ['NUKE_PATH']])

        # --- Tell the user what's up...
        self.env_paths_sanity_check()

    def _tk_aftereffects_env_setup(self):
        """
        Method to set up all the wanted environment
        variables when launching an AE session.
        """
        _setup = '_tk_aftereffects_env_setup'
        self._headers(_setup)

        script_paths = []
        script_paths.append(self._sg_a3_path)
        for script_path in script_paths:
            sys.path.insert(0, script_path)

        # --- Tell the user what's up...
        self.env_paths_sanity_check()

    def _tk_houdini_env_setup(self):
        """
        Method to set up all the wanted environment
        variables when launching a Houdini session.
        """
        _setup = '_tk_aftereffects_env_setup'
        self._headers(_setup)

        script_paths = []
        script_paths.append(self._sg_a3_path)
        for script_path in script_paths:
            sys.path.insert(0, script_path)

        # --- Tell the user what's up...
        self.env_paths_sanity_check()

    def _tk_natron_env_setup(self):
        """
        Method to set up all the wanted environment
        variables when launching a Houdini session.
        """
        _setup = '_tk_natron_env_setup'
        self._headers(_setup)

        script_paths = []

        # --- NOTE: switch to the commented out line in the near future,
        # ---       'X:/tools/natron' is temporary...
        #studio_na_root = '{}/natron'.format(self._repo_path).replace('/', '\\')
        studio_na_root = 'X:/tools/natron'
        script_paths.append(studio_na_root)
        script_paths.append('{}/tools_sse'.format(studio_na_root))
        script_paths.append('{}/tools_sse/Plugins'.format(studio_na_root))
        script_paths.append(self._sg_a3_path)
        studio_na_paths = os.pathsep.join(script_paths)

        if 'NATRON_PLUGIN_PATH' in os.environ:
            logger.debug('Found existing NATRON_PLUGIN_PATH in os.environ...')
            os.environ['NATRON_PLUGIN_PATH'] = os.pathsep.join([studio_na_paths,
                os.environ['NATRON_PLUGIN_PATH']])
        else:
            logger.debug('No existing NATRON_PLUGIN_PATH in os.environ, creating...')
            os.environ['NATRON_PLUGIN_PATH'] = '{}'.format(studio_na_paths)

        # --- Tell the user what's up...
        self.env_paths_sanity_check()

    def _headers(self, user_title):
        """
        Print strings formatted as headers (with
        emphasis) to the console.
        @param str user_title: The title as a string to
                               fromat and print as a
                               header.
        """
        if user_title:
            logger.debug(my_sep)
            logger.debug(user_title)
            logger.debug(my_sep)
        else:
            logger.debug('Please provide a title string.')

    def env_paths_sanity_check(self):
        '''
        Print the lists of source paths to the Shotgun
        Desktop Console.
        @param str engine_setup: represents the DCC setup
                                 we want to check against,
                                 which may have unique
                                 path variables.
        '''
        env_var_str = []

        path_list = ['SYSTEM PATH',
                    'PYTHONPATH',
        ]

        # --- Per engine checks if required...
        if self._engine_name == 'tk-maya':
            _maya_paths = [
                'MAYA_MODULE_PATH',
                'MAYA_PLUG_IN_PATH',
                'MAYA_SCRIPT_PATH'
            ]

            path_list.extend(_maya_paths)

        if self._engine_name == 'tk-nuke':
            _nuke_paths = [
                'NUKE_PATH'
            ]
            path_list.extend(_nuke_paths)

        if self._engine_name == 'tk-aftereffects':
            pass

        if self._engine_name == 'tk-houdini':
            pass

        if self._engine_name == 'tk-natron':
            _natron_paths = [
                'NATRON_PLUGIN_PATH',
            ]
            path_list.extend(_natron_paths)

        # --- Iterate over the paths...
        for path_item in path_list:
            env_var_str.append(my_sep)
            env_var_str.append(path_item)
            env_var_str.append(my_sep)

            if path_item == 'SYSTEM PATH':
                logger.debug('path_item: {}'.format(path_item))
                for item in sys.path:
                    env_var_str.append(item)
            else:
                for item in os.environ[path_item].split(';'):
                    env_var_str.append(item)

        env_var_str.append(my_sep)

        for env_var_item in env_var_str:
            logger.debug(env_var_item)
