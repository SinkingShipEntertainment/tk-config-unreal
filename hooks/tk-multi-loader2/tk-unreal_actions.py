# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

"""
Hook that loads defines all the available actions, broken down by publish type.
"""

import pprint
import os
import sgtk
import unreal
import re
import client_config
import name_enforcer_utility

HookBaseClass = sgtk.get_hook_baseclass()


class UnrealActions(HookBaseClass):

    ##############################################################################################################
    # public interface - to be overridden by deriving classes

    def _import_to_content_browser(self, path, sg_publish_data):
        """
        Import the asset into the Unreal Content Browser.

        :param path: Path to file.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """

        # --- SSE: Use custom framework when loading in content. -AB (2021-06-11)
        imgspc_fw = self.load_framework("tk-framework-imgspc")
        imgspc_ue_imp = imgspc_fw.import_module("unreal.import_utils")
        imgspc_ue_imp.import_to_content_browser(path, sg_publish_data)

        # move the materials to the "Materials" folder
        imgspc_ue_imp.relocate_materials(sg_publish_data)

        # import in the groom information after bringing in the FBX
        ue_import_type = imgspc_ue_imp.get_ue_import_type(sg_publish_data)
        if ue_import_type == unreal.FBXImportType.FBXIT_SKELETAL_MESH:
            imported_grm_obj_paths = imgspc_ue_imp.import_associated_grooms(sg_publish_data)
            imported_texture_paths = imgspc_ue_imp.import_associated_textures(sg_publish_data)

            # bind the groom
            skm_destination_path, skm_destination_name = imgspc_ue_imp.get_destination_path_and_name(
                path, sg_publish_data)
            skeletal_mesh_obj_path = '{0}/{1}.{1}'.format(skm_destination_path, skm_destination_name)
            for grm_obj_path in imported_grm_obj_paths:

                # get the groom package path from the groom object path
                asset_reg = unreal.AssetRegistryHelpers.get_asset_registry()
                groom_asset_data = asset_reg.get_asset_by_object_path(grm_obj_path)
                groom_package = groom_asset_data.package_name.__str__()
                groom_package_path = groom_asset_data.package_path.__str__()
                groom_name = groom_asset_data.asset_name.__str__()

                # form the binding path
                grm_bind_dst, grm_bind_name = imgspc_ue_imp.get_groom_binding_destination_path_and_name(
                    groom_package_path, groom_name)
                grm_binding_path = '%s/%s' % (grm_bind_dst, grm_bind_name)

                # check if the GroomBinding exists and delete if it does
                is_deleted = imgspc_ue_imp.delete_groom_binding(grm_binding_path)
                if not is_deleted:
                    unreal.log_warning('Groom binding not deleted there may be duplicates: %s' %
                                       grm_binding_path)

                # create the binding
                imgspc_ue_imp.create_groom_binding(grm_obj_path, skeletal_mesh_obj_path,
                                                   grm_binding_path)

        # create groom binding after groom import
        if ue_import_type == unreal.GroomGeometryType.STRANDS:

            grm_dst_path, grm_dst_name = imgspc_ue_imp.get_groom_destination_path_and_name(
                path
            )
            grm_obj_path = '{0}/{1}.{1}'.format(grm_dst_path, grm_dst_name, grm_dst_name)

            # get the groom package path from the groom object path
            asset_reg = unreal.AssetRegistryHelpers.get_asset_registry()
            groom_asset_data = asset_reg.get_asset_by_object_path(grm_obj_path)
            groom_package_path = groom_asset_data.package_path.__str__()
            groom_name = groom_asset_data.asset_name.__str__()

            # form the binding path
            grm_bind_dst, grm_bind_name = imgspc_ue_imp.get_groom_binding_destination_path_and_name(
                groom_package_path, groom_name)
            grm_binding_path = '%s/%s' % (grm_bind_dst, grm_bind_name)

            # check if the GroomBinding exists and delete if it does
            is_deleted = imgspc_ue_imp.delete_groom_binding(grm_binding_path)
            if not is_deleted:
                unreal.log_warning('Groom binding not deleted there may be duplicates: %s' %
                                   grm_binding_path)

            # TODO: I am expecting the skeletal mesh to be in the parent directory of the groom
            #  directory. A better way may be getting a context from the groom publish and using
            #  that to build the SkeletalMesh obj path
            # get the object path for the associated skeletal mesh
            asset_list = unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_path(
                '/'.join(grm_dst_path.split('/')[:-1])
            )
            skeletal_mesh_obj_paths = [str(x.object_path) for x in asset_list
                                       if x.asset_class == 'SkeletalMesh']

            if not skeletal_mesh_obj_paths:
                unreal.log_warning('There is no skeletal mesh to bind %s groom to.' % groom_name)
                return

            skeletal_mesh_obj_path = skeletal_mesh_obj_paths[0]

            unreal.log('Groom binding path is: %s' % grm_binding_path)
            unreal.log('Skeletal mesh object path is: %s' % skeletal_mesh_obj_path)

            # create the binding
            imgspc_ue_imp.create_groom_binding(grm_obj_path, skeletal_mesh_obj_path,
                                               grm_binding_path)
