'''This class takes in a DEM image and a color mapping file in the form
   GdalModule(<input_dem> <color_text_file>)
   The script runs the gdaldem hillshade on the image, then runs gdaldem color_relief_map
   on the image. Once a hillshade and color_relief have been generated the hsv_merge script
   is called to merge the hillshade and color_relief together. This script produces 3 output
   images out_hillshade.tiff, out_color.tiff, and DTM_TEXTURE.tiff'''


import sys
import subprocess
from sys import platform as _platform


class GDALDriver(object):

    input_dem = []
    color_text_file = []

    def __init__(self, input_dem, color_text_file):
        self.input_dem = input_dem
        self.color_text_file = color_text_file

    def gdal_hillshade(self):

    #  Run gdaldem hillshade on the input dem image
        if _platform == "win32":
            hill_sh = 'OSGeo4W gdaldem hillshade '+self.input_dem+ ' out_hillshade.tiff'
        else:
            hill_sh = 'gdaldem hillshade '+self.input_dem+ ' out_hillshade.tiff'
        print('Running Command: ', hill_sh)
        try:
            sub_proc1 = subprocess.Popen(hill_sh, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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

        except subprocess.SubprocessError as e:
            print('Error: ' + e)
            print('\nFailed to spawn subprocess for gdal hill-shade')
            sys.exit(1)
        print('\n'+'Hill-Shade created.')

    def gdal_color_relief(self):
    #   Run gdal color_relief on the input dem image using the color_txt_file supplied
        if _platform == "win32":
            col_rel = 'OSGeo4W gdaldem color-relief '+self.input_dem+' '+self.color_text_file+' '+'out_color.tiff'
        else:
            col_rel = 'gdaldem color-relief '+self.input_dem+' '+self.color_text_file+' '+'out_color.tiff'
        print('Running Command:', col_rel)
        try:
            sub_proc2 = subprocess.Popen(col_rel, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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

        except subprocess.SubprocessError as e:
            print('Error: ' + e)
            print('\nFailed to spawn subprocess for gdal color-relief')
            sys.exit(1)
        print('\n'+'Color-Relief created.')

    def hsv_merge(self, merge_location, texture_location):
    #   Merge the hillshade and color-relief using the hsv_merge script
        if _platform == "win32":
            merge = 'OSGeo4W python ' + merge_location+' out_color.tiff out_hillshade.tiff ' + texture_location
        else:
            merge = 'python ' + merge_location+' out_color.tiff out_hillshade.tiff ' + texture_location
        print('Running Command:', merge)
        print('This process takes a while. Please be patient...')
        try:
            sub_proc3 = subprocess.Popen(merge, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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


        except subprocess.SubprocessError as e:
            print('Error' + e)
            print('\nFailed to spawn subprocess for hsv_merge.')
            sys.exit(1)

    def gdal_clean_up(self):
        if _platform == "win32":
            clean = 'del out_hillshade.tiff out_color.tiff'
            print('\nCleaning up Gdal temp images...')
            try:
                subprocess.Popen(clean, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError as e:
                print('Error: ' + e)
                print('\nFailed to clean up GDAL temp images.')
                sys.exit(1)

        else:
            clean = 'rm out_hillshade.tiff out_color.tiff'
            print('\nCleaning up Gdal temp images...')
            try:
                subprocess.Popen(clean, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError as e:
                print('Error: ' + e)
                print('\nFailed to clean up GDAL temp images.')
                sys.exit(1)