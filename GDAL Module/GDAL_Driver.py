#! /usr/bin/env python3.3

'''This class takes in a DEM image and a color mapping file in the form
   GdalModule(<input_dem> <color_text_file>)
   The script runs the gdaldem hillshade on the image, then runs gdaldem color_relief_map
   on the image. Once a hillshade and color_relief have been generated the hsv_merge script
   is called to merge the hillshade and color_relief together. This script produces 3 output
   images out_hillshade.tif, out_color.tif, and DTM_TEXTURE.tif'''

import sys
import subprocess


class GdalDriver(object):

    input_dem = []
    color_text_file = []

    def __init__(self, input_dem, color_text_file):
        self.input_dem = input_dem
        self.color_text_file = color_text_file

    def gdal_hillshade(self):

    #  Run gdaldem hillshade on the input dem image
        hill_sh = 'gdaldem hillshade '+ self.input_dem + ' out_hillshade.tif'
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
        except:
            print('Failed to spawn subprocess for gdal hill-shade')
            sys.exit(1)
        print('\n'+'Hill-Shade created.')

    def gdal_color_relief(self):
    #   Run gdal color_relief on the input dem image using the color_txt_file supplied
        col_rel = 'gdaldem color-relief '+self.input_dem+' '+self.color_text_file+' '+'out_color.tif'
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
        except:
            print('Failed to spawn subprocess for gdal color-relief')
            sys.exit(1)
        print('\n'+'Color-Relief created.')

    def hsv_merge(self):
    #   Merge the hillshade and color-relief using the hsv_merge script
        merge = 'python hsv_merge.py out_color.tif out_hillshade.tif DTM_TEXTURE.tif'
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
                raise Exception('hsv_merge failed - check console for errors.')
        except:
            print('Failed to spawn subprocess for hsv_merge.')
            sys.exit(1)

    #   Let the user know we are done and the images have been created and merged
        print('Process Complete.')
