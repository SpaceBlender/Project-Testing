import bpy
from bpy.props import *
from bpy_extras.io_utils import ImportHelper
from . import blender_module
from . import gdal_module
from sys import platform as _platform
import os


class UI_Driver(bpy.types.Operator, ImportHelper):
    bl_idname = "import_dem.img"
    bl_label  = "Import DEM from IMG (.IMG)"
    bl_options = {'UNDO'}
    filter_glob = StringProperty(default="*.IMG", options={'HIDDEN'})

    #Color Control consider an option to say if you have GDAL installed or not -- possibly detect GDAL
    # Colors to possibly add
    #('BrownAndRedColorPattern', "Brown & Red (Mars)", "Not colorblind friendly")
    #('GrayscaleColorPattern', "Grayscale (8-16 bit grays, Lunar)", "Colorblind friendly")
    color_pattern = EnumProperty( items=(
        ('NoColorPattern', "None", "Will skip GDAL execution"),
        ('Rainbow_Saturated', 'Rainbow Saturated', 'Colorblind friendly'),
        ('Rainbow_Medium', 'Rainbow Medium', 'Colorblind friendly'),
        ('Rainbow_Light', 'Rainbow Light', 'Colorblind friendly'),
        ('Blue_Steel', 'Blue Steel', 'Colorblind friendly'),
        ('Earth', 'Earth', 'Colorblind friendly'),
        ('Diverging_BrownBlue', 'Diverging Brown & Blue', 'Colorblind friendly'),
        ('Diverging_RedGray', 'Diverging Red & Gray', 'Colorblind friendly'),
        ('Diverging_BlueRed', 'Diverging Blue & Red', 'Colorblind friendly'),
        ('Diverging_RedBlue', 'Diverging Red & Blue', 'Colorblind friendly'),
        ('Diverging_GreenRed', 'Diverging Green & Red', 'Colorblind friendly'),
        ('Sequential_Blue', 'Sequential Blue', 'Colorblind friendly'),
        ('Sequential_Green', 'Sequential Green', 'Colorblind friendly'),
        ('Sequential_Red', 'Sequential Red', 'Colorblind friendly'),
        ('Sequential_BlueGreen', 'Sequential Blue & Green', 'Colorblind friendly'),
        ('Sequential_YellowBrown', 'Sequential Yellow & Brown', 'Colorblind friendly')),
                                  name="Color", description="Import Color Texture", default='NoColorPattern')

    #Flyover Pattern Control
    flyover_pattern = EnumProperty(items=(
        ('NoFlyover', "No flyover", "Don't ceate a flyover"),
        ('AlgorithmicPattern', "Algorithmic Pattern", "Automatically create a 'pretty' flyover"),
        ('CirclePattern', "Circle Pattern", "Create a generic circular flyover"),
        ('OvularPattern', "Ovular Pattern", "Create a generic ovular flyover"),
        ('HourGlassPattern', "Hour Glass Pattern", "Create a generic X like flyover"),
        ('DiamondPattern', "Diamond Pattern", "Create a diagonal flyover"),
        ('TriangularPattern', "Triangular Pattern", "Create a diagonal flyover"),
        ('LinearPattern', "Linear Pattern", "Create a linear flyover")),
                                   name="Flyover", description="Import Flyover", default='NoFlyover')

    #Scaling Control
    scale = FloatProperty(name="Scale",
                          description="Scale the IMG",
                          min=0.0001,
                          max=10.0,
                          soft_min=0.001,
                          soft_max=100.0,
                          default=0.01)
    bin_mode = EnumProperty(items=(
        ('NONE', "None", "Don't bin the image"),
        ('BIN2', "2x2", "use 2x2 binning to import the mesh"),
        ('BIN6', "6x6", "use 6x6 binning to import the mesh"),
        ('BIN6-FAST', "6x6 Fast", "use one sample per 6x6 region"),
        ('BIN12', "12x12", "use 12x12 binning to import the mesh"),
        ('BIN12-FAST', "12x12 Fast", "use one sample per 12x12 region")),
                            name="Binning", description="Import Binning", default='BIN12-FAST')

    def execute(self, context):
        input_DEM = self.filepath
        input_DEM = bpy.path.ensure_ext(input_DEM, '.IMG')
        dtm_location = self.filepath
        texture_location = os.path.expanduser('~/DTM_TEXTURE.tiff')
        texture_location = os.getcwd() + '/DTM_TEXTURE.tiff'

        ################################################################################
        ## Use the GDAL tools to create hill-shade and color-relief and merge them with
        ## hsv_merge.py to use as a texture for the DTM. Creates DTM_TEXTURE.tiff
        ################################################################################
        # Strip out the image name to set texture location
        texture_location = self.filepath.split('/')[-1:]
        texture_location = texture_location[0].split('.')[:1]
        texture_location = os.getcwd()+'/'+texture_location[0]+'.tiff'


        if self.color_pattern == 'NoColorPattern':
            pass
        else:
            # If user selected a colr we are going to run the gdal and merge processes
            # We need to dtermine which OS is being used and set the location of color files
            # and the merge script accordingly
            if _platform == "linux" or _platform == "linux2":
            # linux
                color_file = '/usr/share/blender/scripts/addons/USGS/color_maps/' + self.color_pattern + '.txt'
                merge_location = '/usr/share/blender/scripts/addons/USGS/hsv_merge.py'
            elif _platform == "darwin":
            # OS X
                color_file = '/Applications/Blender/blender.app/Contents/MacOS/2.69/scripts/addons/USGS/color_maps/'\
                    + self.color_pattern + '.txt'
                merge_location = '/Applications/Blender/blender.app/Contents/MacOS/2.69/scripts/addons/USGS/hsv_merge.py'
            elif _platform == "win32":
            # Windows.
                pass

            gdal = gdal_module.GDALDriver(dtm_location, color_file)
            gdal.gdal_hillshade()
            gdal.gdal_color_relief()
            gdal.hsv_merge(merge_location, texture_location)
            print('\nSaving texture at: ' + texture_location)
            gdal.gdal_clean_up()
        ################################################################################
        return blender_module.load(self, context,
                                   filepath=self.filepath,
                                   scale=self.scale,
                                   bin_mode=self.bin_mode,
                                   color_pattern=self.color_pattern,
                                   flyover_pattern=self.flyover_pattern,
                                   texture_location=texture_location,
                                   cropVars=False,
                                   )
        #return {'CANCELLED'}