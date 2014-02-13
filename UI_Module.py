import bpy
from bpy.props import *
from bpy_extras.io_utils import ImportHelper

class UI_Driver(bpy.types.Operator, ImportHelper):
    bl_idname = "import_dem.img"
    bl_label  = "Import DEM from IMG (.IMG)"
    bl_options = {'UNDO'}
    filter_glob = StringProperty(default="*.IMG", options={'HIDDEN'})

    #Color Control consider an option to say if you have GDAL installed or not -- possibly detect GDAL
    color_pattern = EnumProperty( items=(
        ('NoColorPattern', "None", "Will skip GDAL execution"),
        ('GrayscaleColorPattern', "Grayscale (8-16 bit grays, Lunar)", "Colorblind friendly"),
        ('BlueAndWhiteColorPattern', "Blues & Whites (default)", "Colorblind friendly"),
        ('BrownAndBlueColorPattern', "Brown & Blue (Earthlike)", "Colorblind friendly"),
        ('BrownAndRedColorPattern', "Brown & Red (Mars)", "Not colorblind friendly"),
        ('RainbowColorPattern', "Rainbow", "Extremely unfriendly to the colorblind")),
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