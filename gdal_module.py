'''This class takes in a DEM image and a color mapping file in the form
   GdalModule(<input_dem> <color_text_file>)
   The script runs the gdaldem hillshade on the image, then runs gdaldem color_relief_map
   on the image. Once a hillshade and color_relief have been generated the hsv_merge script
   is called to merge the hillshade and color_relief together. This script produces 3 output
   images out_hillshade.tiff, out_color.tiff, and DTM_TEXTURE.tiff'''


import sys
import subprocess


class GDALDriver(object):

    input_dem = []
    color_text_file = []

    def __init__(self, input_dem, color_text_file):
        self.input_dem = input_dem
        self.color_text_file = color_text_file

    def gdal_hillshade(self):

    #  Run gdaldem hillshade on the input dem image
        hill_sh = 'gdaldem hillshade '+self.input_dem+ ' out_hillshade.tiff'
        print('Running Command: ', hill_sh)
        try:
            sub_proc1 = subprocess.Popen(hill_sh, close_fds=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        #   Print the progress of the GDAL operation to the console to give user feedback
            while sub_proc1.poll() is None:
                out = sub_proc1.stdout.read(1)
                if out != '':
                    outstr = str(out)
                    for char in outstr:
                        if char in " b'":
                            outstr = outstr.replace(char, '')
                    sys.stdout.write(outstr)
                    sys.stdout.flush()

            #Check if GDAL returns an error message, then we print GDAL's error message and exit the program
            for line in sub_proc1.stderr:
                print('gdaldem hillshade failed.'+'\n' + str(line))
                sys.exit(1)
        except subprocess.SubprocessError as e:
            print('Error: ' + e)
            print('\nFailed to spawn subprocess for gdal hill-shade')
            sys.exit(1)
        print('\n'+'Hill-Shade created.')

    def gdal_color_relief(self):
    #   Run gdal color_relief on the input dem image using the color_txt_file supplied
        col_rel = 'gdaldem color-relief '+self.input_dem+' '+self.color_text_file+' '+'out_color.tiff'
        print('Running Command:', col_rel)
        try:
            sub_proc2 = subprocess.Popen(col_rel, close_fds=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            #Print the progress of the GDAL operation to the console to give user feedback
            while sub_proc2.poll() is None:
                out = sub_proc2.stdout.read(1)
                if out != '':
                    outstr = str(out)
                    for char in outstr:
                        if char in " b'":
                            outstr = outstr.replace(char, '')
                    sys.stdout.write(outstr)
                    sys.stdout.flush()
        #   Check if GDAL returns an error message, then we print GDAL's error message and exit the program.
            for line in sub_proc2.stderr:
                print('gdaldem color-relief failed.'+'\n' + str(line))
                sys.exit(1)
        except subprocess.SubprocessError as e:
            print('Error: ' + e)
            print('\nFailed to spawn subprocess for gdal color-relief')
            sys.exit(1)
        print('\n'+'Color-Relief created.')

    def hsv_merge(self, merge_location, texture_location):
    #   Merge the hillshade and color-relief using the hsv_merge script
        merge = 'python ' + merge_location+' out_color.tiff out_hillshade.tiff ' + texture_location
        print('Running Command:', merge)
        print('This process takes a while. Please be patient...')
        try:
            sub_proc3 = subprocess.Popen(merge, close_fds=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        #   Print the progress of the hsv_merge operation to the console to give user feedback
            while sub_proc3.poll() is None:
                out = sub_proc3.stdout.read(1)
                if out != '':
                    outstr = str(out)
                    for char in outstr:
                        if char in " b'":
                            outstr = outstr.replace(char, '')
                    sys.stdout.write(outstr)
                    sys.stdout.flush()

            if sub_proc3.returncode:
                raise Exception('\nhsv_merge failed - check console for errors.')
        except subprocess.SubprocessError as e:
            print('Error' + e)
            print('\nFailed to spawn subprocess for hsv_merge.')
            sys.exit(1)

    def gdal_clean_up(self):
        clean = 'rm out_hillshade.tiff out_color.tiff'
        print('\nCleaning up Gdal temp images...')
        try:
            subprocess.Popen(clean, close_fds=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            print('Error: ' + e)
            print('\nFailed to clean up GDAL temp images.')
            sys.exit(1)

###################################################################################################################

# Test Area Caution!!

###################################################################################################################
# gdal = GDALDriver('/Users/jasonhedlund/Desktop/DEMs/DTEEC_009842_1755_009130_1755_A01.IMG', '/Applications/Blender/blender.app/Contents/MacOS/2.69/scripts/addons/USGS/color_maps/Diverging_BlueRed.txt')
# gdal.gdal_hillshade()
# gdal.gdal_color_relief()
# gdal.hsv_merge('/Applications/Blender/blender.app/Contents/MacOS/2.69/scripts/addons/USGS/hsv_merge.py', '/Users/jasonhedlund/Desktop/processed_DEMs/DTEEC_009842_1755_009130_1755_A01.tiff')
# #print('\nSaving texture at: ' + texture_location)
# gdal.gdal_clean_up()