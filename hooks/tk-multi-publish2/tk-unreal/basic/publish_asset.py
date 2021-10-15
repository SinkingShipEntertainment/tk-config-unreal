# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license 
# file included in this repository.

import sgtk
import os
import stat
import unreal
import datetime
import imgspc_asset_utility
from P4 import P4
import json
import SSP4
import SGHelpers
import shutil

HookBaseClass = sgtk.get_hook_baseclass()

class UnrealAssetPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an Unreal asset.

    This hook relies on functionality found in the base file publisher hook in
    the publish2 app and should inherit from it in the configuration. The hook
    setting for this plugin should look something like this::

        hook: "{self}/publish_file.py:{engine}/tk-multi-publish2/basic/publish_session.py"

    To learn more about writing a publisher plugin, visit
    http://developer.shotgunsoftware.com/tk-multi-publish2/plugin.html
    """

    # NOTE: The plugin icon and name are defined by the base file plugin.

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """

        return """Publishes the asset to Perforce. A <b>Publish</b> entry will be
        created in Shotgun which will include a list of files included in the
        perforce publish. The published files will reside in the publish depot
        on Perforce, and will be branched into episodes using the branch mapping
        tool."""

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate, publish and
        finalize methods.

        A dictionary on the following form::

            {
                "Settings Name": {
                    "type": "settings_type",
                    "default": "default_value",
                    "description": "One line description of the setting"
            }

        The type string should be one of the data types that toolkit accepts as
        part of its environment configuration.
        """

        # inherit the settings from the base publish plugin
        base_settings = super(UnrealAssetPublishPlugin, self).settings or {}

        # Here you can add any additional settings specific to this plugin
        new_settings = {
            "Publish Depot": {
                "type": "str",
                "default":  None,
                "description": "The name of the publish depot."
            },
            "Publish Depot Internal Path" :  {
                "type": "str",
                "default": None,
                "description": "The path within the publish depot where the files are stored."
            }
        }     
    
        # update the base settings
        base_settings.update(new_settings)
     
        return base_settings

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["unreal.asset.Blueprint", "unreal.asset.World"]

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin. Only items matching the filters defined via the
        item_filters property will be presented to this method.

        A publish task will be generated for each item accepted here. Returns a
        dictionary with the following booleans:

            - accepted: Indicates if the plugin is interested in this value at
                all. Required.
            - enabled: If True, the plugin will be enabled in the UI, otherwise
                it will be disabled. Optional, True by default.
            - visible: If True, the plugin will be visible in the UI, otherwise
                it will be hidden. Optional, True by default.
            - checked: If True, the plugin will be checked in the UI, otherwise
                it will be unchecked. Optional, True by default.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process

        :returns: dictionary with boolean keys accepted, required and enabled
        """        
        accepted = True
        publisher = self.parent

        # check that we have settings for the depot, and the internal depot path
        publish_depot_setting = settings.get("Publish Depot")
        publish_depot_value = publish_depot_setting.value
        publish_depot_internal_path_setting = settings.get("Publish Depot Internal Path")
        publish_depot_internal_path_value = publish_depot_internal_path_setting.value

        if not publish_depot_value:
            self.logger.debug(
                "A publish depot could not be determined for the "
                "asset item. Not accepting the item."
            )
            accepted = False

        if not publish_depot_internal_path_value:
            self.logger.debug(
                "The internal publish depot path could not be determined for the "
                "asset item. Not accepting the item."
            )
            accepted = False

        return {
            "accepted": accepted,
            "checked": True
        }

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish. Returns a
        boolean to indicate validity.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: True if item is valid, False otherwise.
        """      

        publish_depot = settings.get("Publish Depot").value       
        
        p4 = SSP4.connect_to_perforce()
        if not p4.connected():
            self.logger.error("Not connected to perforce, connect to" +
                " perforce using p4v and try again.")
            return False

        try:
            root_folder = SSP4.set_client_workspace_and_get_root(p4, publish_depot)                            
        except :
            self.logger.error("Could not find your perforce workspace," +
                " connect to perforce using p4v and try again.")
            return False
    
        publish_folder = os.path.join(root_folder, publish_depot)
          
        if not os.path.isdir(publish_folder):
            # NOTE: We're just checking here if the publish depot is in the
            # workspace at all, not if the files we need are actually there.
            # We're basically just assuming that the folder is complete
            # and up-to-date.
            # At some point in the future this might need to be smarter.
            self.logger.error("Could not find publish depot at: "
             + publish_folder 
             + " please get the publish depot in p4v and try again.")
            return False

        # if we got here, we know we can connect to perforce, and have the 
        # publish depot checked out, so we should be good to go.
        # We can just continue with the remaining validation checks.       
        asset_path = item.properties.get("asset_path")
        asset_name = item.properties.get("asset_name")
        if not asset_path or not asset_name:
            self.logger.debug("Asset path or name not configured.")
            return False

        is_valid_asset_name = False
        if asset_name[-3:] == "_BP":
            is_valid_asset_name = True
        if asset_name[-7:].lower() == "_set_lv":
            is_valid_asset_name = True
      
        if not is_valid_asset_name:
            self.logger.debug("Expected <ASSET_NAME>_BP or <ASSET_NAME>_Set_Lv as asset file name.")
            return False

        if item.description == None:
            self.logger.debug("Description of publish is required.")
            return False

        asset_util = imgspc_asset_utility.ImgSpcAssetUtility
        asset_path_for_dependencies = str(asset_path).split(".")[0]
        dependency_json = asset_util.fetch_dependencies(asset_path_for_dependencies);
        dependency_list = json.loads(dependency_json)["fileList"]
        for dep in dependency_list:
             self.logger.debug("Dependency discovered: " + dep)

        # Add the Unreal asset name to the fields
        fields = {"name" : asset_name}

        # Add today's date to the fields
        date = datetime.date.today()
        fields["YYYY"] = date.year
        fields["MM"] = date.month
        fields["DD"] = date.day

        # Stash the Unrea asset path and name in properties
        item.properties["asset_path"] = asset_path
        item.properties["asset_name"] = asset_name
        item.properties["dependency_list"] = dependency_list

        # Set the Published File Type
        item.properties["publish_type"] = "UE Asset"

        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        # set this to true when debugging to disable all the perforce calls.
        debug_skip_perforce = False
        # set this to true to do a dry run of the publish when testing.
        debug_dry_run = False

        # Export the asset from Unreal
        asset_path = item.properties["asset_path"]
        # Remove the last 3 characters (Should be _BP) from the asset name.
        asset_name = item.properties["asset_name"][0:-3] 

        # Grab the settings variables needed to put things into the publish depot
        publish_depot = settings.get("Publish Depot").value       
        publish_depot_internal_path = settings.get("Publish Depot Internal Path").value
        depot_path = "//" + publish_depot + "/" + publish_depot_internal_path + "/"

        sg = self.parent.sgtk.shotgun
        p4 = SSP4.connect_to_perforce()
        root_folder = SSP4.set_client_workspace_and_get_root(p4, publish_depot)

        publish_folder = os.path.join(root_folder, publish_depot)

        # make sure the publish repo is up to date.
        p4.run_sync(publish_folder)

        publish_path = os.path.join(publish_folder, publish_depot_internal_path) + "/"
        publish_path = publish_path.replace("\\\\", "/")
        project_dir = unreal.Paths.project_content_dir()

        # get the list of dependencies for the asset.
        dependency_list = item.properties["dependency_list"]
        source_paths = []
        destination_paths = []
        depot_paths = []
   
        if not debug_skip_perforce:
            change_description = "Unreal Asset Publish: " + item.description
            new_changelist = p4.fetch_change()
            new_changelist._description = change_description

        for dep in dependency_list:
            # We're assuming all files are uassets (So far, this has been true)
            source_paths.append(dep.replace("/Game/", project_dir) + ".uasset")
            destination_paths.append(dep.replace("/Game/", publish_path) + ".uasset")    
            depot_paths.append(dep.replace("/Game/", depot_path) + ".uasset")

            if not debug_skip_perforce:
                if os.path.isfile(destination_paths[-1]):
                    # File exists in the publish depot folder, so assume it's tracked by
                    # perforce and do an "edit" command on it.    
                    if len(p4.run_filelog( destination_paths[-1])) < 1:
                        # perforce sets everything to read-only in its folders,
                        # so let's change the permission to writable before we try to 
                        # copy over the file and add it to perforce
                        os.chmod(destination_paths[-1], stat.S_IWRITE)
                        shutil.copy(source_paths[-1], destination_paths[-1])
                        p4.run("add", destination_paths[-1])
                    else:
                        p4.run("edit", destination_paths[-1])
                        shutil.copy(source_paths[-1], destination_paths[-1])
                else:
                    # File doesn't exist in the publish depot, so use an 
                    # "add" command to add it.
                    destination_directory = os.path.dirname(destination_paths[-1])
                    if not os.path.isdir(destination_directory):
                        os.makedirs(destination_directory)
                    shutil.copy(source_paths[-1], destination_paths[-1])
                    p4.run("add", destination_paths[-1])
        
        if not debug_skip_perforce:                  
            new_changelist._files = depot_paths
            p4.run_submit(new_changelist)
            
        dependency_obj = {"fileList": depot_paths}
        dependency_field_string = json.dumps(dependency_obj)      
      
        asset_id = SGHelpers.get_asset_id_by_name(sg, asset_name, item.context.project)
        try:
            highest_publish_number = SGHelpers.get_highest_publish_number_for_asset(sg, asset_id)
        except:
            highest_publish_number = 0
        new_version = highest_publish_number + 1

        # TODO: Figure out the published_file_type, task, and whether the way version
        # number is being set is okay.

        item.properties["sg_publish_data"] = sgtk.util.register_publish(
            self.parent.sgtk,
            item.context,
            "null",#path
            asset_name,
            new_version,
            comment=item.description,
            thumbnail_path=item.get_thumbnail_as_path(),
            published_file_type=item.properties["publish_type"],
            dry_run=debug_dry_run,
            sg_fields={"sg_unreal_published_file_list": dependency_field_string}
        )

     
    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once all the publish
        tasks have completed, and can for example be used to version up files.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """
        # currently we have nothing we need to do in finalize, so this is
        # left blank