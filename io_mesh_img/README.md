io_mesh_img
===========

PDS IMG mesh importer for Blender3D

Blender used to keep this plugin under "io_mesh_img" but has since moved it to
"io_convert_image_to_mesh" in an effort to better categorize and define plugins.

Installation
============

The contents of the plugin directory are meant to be copied verbatim into the
blender plugins directory into a directory named io_convert_image_to_mesh. 

OSX Eg:
 /Applications/blender.app/Contents/MacOS/2.65/scripts/addons/io_convert_image_to_mesh_img/

Usage
=====

1) Enable the plugin in the user preferences pane. Then a menu option will
appear in the File->Import submenu.

2) Choose an appropriate file and tweak the settings in the settings pane
(usually on the left) before starting the import.

3) Profit.

Hacking note
============

The upstream Blender3D devs will sometimes make subtle changes to the source
in order to keep the plugin working with Blender Python API changes in new
versions of Blender3D. These should be merged before starting to hack on the
plugin.
