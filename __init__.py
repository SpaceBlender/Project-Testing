# ##### BEGIN GPL LICENSE BLOCK #####
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
if "bpy" in locals():
    import imp
    #imp.reload(GDAL_Module)
    imp.reload(UI_Module)
    #imp.reload(Blender_Module)
    #imp.reload(Flyover_Module)
else:
    #from . import Blender_Module
    #from . import Flyover_Module
    from . import UI_Module
    #from . import GDAL_Module

import bpy

bl_info = {
    "name": "Import DEM from IMG",
    "author": "Andrew Carter, Eric Ghazal, Jason Hedlund, Terrence",
    "version": (0, 1, 0),
    "blender": (2, 63, 0),
    "warning": "Requires GDAL to be installed.",
    "location": "File > Import > Import DEM from IMG (.IMG)",
    "description": "Import DEM, apply texture, and create flyover.",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

############################## REGISTRATION #################################
def menu_import(self, context):
    self.layout.operator(UI_Module.UI_Driver.bl_idname, text="Import DEM from IMG (.IMG)")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_import)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_import)

## How to register the script inside of Blender
if __name__ == "__main__":
    register()