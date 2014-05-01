__author__ = "Andrew"

from . import flyover_module
from . import blender_module
import unittest
import math
import bpy

#The DEM you want to use for blender unit tests
dem = 'C:\\Users\\Andrew\\Desktop\\DEMs\\DTEED_020492_1830_021481_1830_A01.IMG'

class TestFlyoverPatterns(unittest.TestCase):
    def test_no_flyover(self):
        #Verify normal pass through
        flyover = flyover_module.FlyoverDriver()
        bool = flyover.no_flyover()
        self.assertTrue(bool)
        TestFlyoverPatterns.cleanup_flyover(self)

    def test_linnear_pattern(self):
        flyover = flyover_module.FlyoverDriver()
        bool = flyover.linear_pattern()
        self.assertTrue(bool)
        TestFlyoverPatterns.cleanup_flyover(self)

    def test_diamond_pattern(self):
        flyover = flyover_module.FlyoverDriver()
        bool = flyover.diamond_pattern()
        self.assertTrue(bool)
        TestFlyoverPatterns.cleanup_flyover(self)

    def test_circle_pattern(self):
        flyover = flyover_module.FlyoverDriver()
        bool = flyover.circle_pattern()
        self.assertTrue(bool)
        TestFlyoverPatterns.cleanup_flyover(self)

    #Wasn't needed in the normal flyover but i provdided this here since there will be multiple flyovers constructed
    def cleanup_flyover(self):
        #Delete the Camera, CameraTarget, and the Path
        for item in bpy.data.objects:
            if item.type == 'CAMERA':
                item.select = True
                bpy.ops.object.delete()
            if item.type == 'EMPTY':
                item.select = True
                bpy.ops.object.delete()
            if item.type == 'CURVE':
                item.select = True
                bpy.ops.object.delete()


class TestMiscellaneousFunctions(unittest.TestCase):
    def test_distance_two_points_x_test(self):
        flyover = flyover_module.FlyoverDriver()

        point_one = (1.0, 0.0, 0.0)
        point_two = (0.0, 0.0, 0.0)

        val = flyover.distance_two_points(point_one, point_two)
        self.assertAlmostEquals(1.0, val)

    def test_distance_two_points_y_test(self):
        flyover = flyover_module.FlyoverDriver()

        point_one = (0.0, 1.0, 0.0)
        point_two = (0.0, 0.0, 0.0)

        val = flyover.distance_two_points(point_one, point_two)
        self.assertAlmostEquals(1.0, val)

    def test_distance_two_points_z_test(self):
        flyover = flyover_module.FlyoverDriver()

        point_one = (0.0, 0.0, 1.0)
        point_two = (0.0, 0.0, 0.0)

        val = flyover.distance_two_points(point_one, point_two)
        self.assertAlmostEquals(1.0, val)

    def test_distance_two_points_normal_usage(self):
        flyover = flyover_module.FlyoverDriver()

        point_one = (1.0, 1.0, 2.0)
        point_two = (0.0, -1.0, -1.0)

        val = flyover.distance_two_points(point_one, point_two)
        self.assertAlmostEquals( math.sqrt(14.0), val)

    def test_midpoint_two_points_x(self):
        flyover = flyover_module.FlyoverDriver()

        point_one = (2.0, 0.0, 0.0)
        point_two = (0.0, 0.0, 0.0)

        val = flyover.midpoint_two_points(point_one, point_two)
        self.assertAlmostEqual(val[0], 1.0)
        self.assertAlmostEqual(val[1], 0.0)
        self.assertAlmostEqual(val[2], 0.0)

    def test_midpoint_two_points_y(self):
        flyover = flyover_module.FlyoverDriver()

        point_one = (0.0, 2.0, 0.0)
        point_two = (0.0, 0.0, 0.0)

        val = flyover.midpoint_two_points(point_one, point_two)
        self.assertAlmostEqual(val[0], 0.0)
        self.assertAlmostEqual(val[1], 1.0)
        self.assertAlmostEqual(val[2], 0.0)

    def test_midpoint_two_points_z(self):
        flyover = flyover_module.FlyoverDriver()

        point_one = (0.0, 0.0, 2.0)
        point_two = (0.0, 0.0, 0.0)

        val = flyover.midpoint_two_points(point_one, point_two)
        self.assertAlmostEqual(val[0], 0.0)
        self.assertAlmostEqual(val[1], 0.0)
        self.assertAlmostEqual(val[2], 1.0)

    def test_midpoint_two_points_general_usage(self):
        flyover = flyover_module.FlyoverDriver()

        point_one = (4.0, 2.0, 2.0)
        point_two = (2.0, -2.0, -1.0)

        val = flyover.midpoint_two_points(point_one, point_two)
        self.assertAlmostEqual(val[0], 3.0)
        self.assertAlmostEqual(val[1], 0.0)
        self.assertAlmostEqual(val[2], 0.5)

    #This one seemed really odd to me, i got lost analyzing what data was being passed in...
    #Not really sure why the midpoint of midpoints ends up being the actual midpoint...
    #The image might be skewed...
    def test_get_center_general_usage(self):
        flyover = flyover_module.FlyoverDriver()

        x_cross_mid = (100.0-0.0)/2
        y_cross_mid = (100.0-0.0)/2

        val = flyover.get_center(((100.0,0.0,0.0),(0.0,0.0,0.0),(0.0,100.0,0.0),(0.0,0.0,0.0)))
        self.assertAlmostEqual(x_cross_mid/2, val[0]) #x pos
        self.assertAlmostEqual(y_cross_mid/2, val[1]) #y pos

    #Warning: these values had to be hard coded
    #If you don't have this DEM then you may spend a lot of time getting this test to work correctly.
    def test_get_dem_boundaries_normal_dem(self):
        #Load in a DTM (we need some type of mesh!)
        blender_module.DTMViewerRenderContext.clearScene(self)
        blender_module.load(self, None,
             filepath=dem,
             scale=0.01,
             bin_mode='BIN12-FAST',
             color_pattern='None',
             flyover_pattern='No flyover',
             texture_location=None,
             cropVars=False,
             resolution='1080p',
             stars=False,
             mist=False)

        #Fetch the dem_boundaries
        flyover = flyover_module.FlyoverDriver()
        vals = flyover.get_dem_boundaries()
        x_max = vals[0]
        #check x y z positions
        self.assertAlmostEqual(x_max[0], 31.92000007)
        self.assertAlmostEqual(x_max[1], -51.9000015)
        self.assertAlmostEqual(x_max[2], 5.97231769)

        x_min = vals[1]
        self.assertAlmostEqual(x_min[0], 0.0)
        self.assertAlmostEqual(x_min[1], -3.18000006)
        self.assertAlmostEqual(x_min[2], 1.376258969)

        y_max = vals[2]
        self.assertAlmostEqual(y_max[0], 25.92000007)
        self.assertAlmostEqual(y_max[1], 0.0)
        self.assertAlmostEqual(y_max[2], 6.119607925)

        y_min = vals[3]
        self.assertAlmostEqual(y_min[0], 6.42000007)
        self.assertAlmostEqual(y_min[1], -55.13999938)
        self.assertAlmostEqual(y_min[2], 6.86862039)

        blender_module.DTMViewerRenderContext.clearScene(self)

    #Small Scale
    def test_get_dem_boundaries_small_resolution(self):
       #Load in a DTM (we need some type of mesh!)
        blender_module.DTMViewerRenderContext.clearScene(self)
        blender_module.load(self, None,
             filepath=dem,
             scale=0.001,
             bin_mode='BIN12-FAST',
             color_pattern='None',
             flyover_pattern='No flyover',
             texture_location=None,
             cropVars=False,
             resolution='180p',
             stars=False,
             mist=False)

        #Fetch the dem_boundaries
        flyover = flyover_module.FlyoverDriver()
        vals = flyover.get_dem_boundaries()
        x_max = vals[0]
        #check x y z positions
        self.assertAlmostEqual(x_max[0], 3.1919999)
        self.assertAlmostEqual(x_max[1], -5.18400001)
        self.assertAlmostEqual(x_max[2], 5.97231769)

        x_min = vals[1]
        self.assertAlmostEqual(x_min[0], 0.0)
        self.assertAlmostEqual(x_min[1], -3.18000006)
        self.assertAlmostEqual(x_min[2], 1.376258969)

        y_max = vals[2]
        self.assertAlmostEqual(y_max[0], 25.92000007)
        self.assertAlmostEqual(y_max[1], 0.0)
        self.assertAlmostEqual(y_max[2], 6.119607925)

        y_min = vals[3]
        self.assertAlmostEqual(y_min[0], 6.42000007)
        self.assertAlmostEqual(y_min[1], -55.13999938)
        self.assertAlmostEqual(y_min[2], 6.86862039)

    #Massive scale
    def test_get_dem_boundaries_big_resolution(self):
       #Load in a DTM (we need some type of mesh!)
        blender_module.DTMViewerRenderContext.clearScene(self)
        blender_module.load(self, None,
             filepath=dem,
             scale=1.0,
             bin_mode='BIN12-FAST',
             color_pattern='None',
             flyover_pattern='No flyover',
             texture_location=None,
             cropVars=False,
             resolution='1080p',
             stars=False,
             mist=False)

        #Fetch the dem_boundaries
        flyover = flyover_module.FlyoverDriver()
        vals = flyover.get_dem_boundaries()
        x_max = vals[0]
        #check x y z positions
        self.assertAlmostEqual(x_max[0], 3192.0)
        self.assertAlmostEqual(x_max[1], -5184.0)
        self.assertAlmostEqual(x_max[2], 5.97231769)

        x_min = vals[1]
        self.assertAlmostEqual(x_min[0], 0.0)
        self.assertAlmostEqual(x_min[1], -3.18000006)
        self.assertAlmostEqual(x_min[2], 1.376258969)

        y_max = vals[2]
        self.assertAlmostEqual(y_max[0], 25.92000007)
        self.assertAlmostEqual(y_max[1], 0.0)
        self.assertAlmostEqual(y_max[2], 6.119607925)

        y_min = vals[3]
        self.assertAlmostEqual(y_min[0], 6.42000007)
        self.assertAlmostEqual(y_min[1], -55.13999938)
        self.assertAlmostEqual(y_min[2], 6.86862039)