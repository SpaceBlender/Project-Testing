__author__ = 'Andrew'
from . import blender_module
import bpy
import unittest
import bpy.props

class TestBlenderDTMViewerRenderContext(unittest.TestCase):
    def setUp(self):
        pass

    #unit test test the whole function which acts as a toggle
    #it insures that the variables are switched as expected
    #this would have been broken into several tests, but the stars function has no break down
    def test_stars(self):
        world = bpy.context.scene.world
        render = blender_module.DTMViewerRenderContext('C:\\Users\\Andrew\\Desktop\\DEMs\\DTEED_020492_1830_021481_1830_A01.IMG','1080p',True, False)

        [r, g, b] = world.zenith_color
        self.assertNotEqual([r, g, b], [0.040, 0.040, 0.040])
        self.assertNotEqual(world.use_sky_paper, True)
        self.assertNotEqual(world.use_sky_blend, True)
        self.assertNotEqual(world.use_sky_real, True)

        render.createStars()
        [r, g, b] = world.horizon_color
        self.assertAlmostEqual(r, 0.0)
        self.assertAlmostEqual(g, 0.0)
        self.assertAlmostEqual(b, 0.0)

        [r, g, b] = world.zenith_color
        self.assertAlmostEqual(r, 0.040)
        self.assertAlmostEqual(g, 0.040)
        self.assertAlmostEqual(b, 0.040)

        self.assertEqual(world.use_sky_paper, True)
        self.assertEqual(world.use_sky_blend, True)
        self.assertEqual(world.use_sky_real, True)
        self.assertEqual(world.star_settings.use_stars, True)

        TestBlenderDTMViewerRenderContext.cleanup(self)

    # def test_mist(self):
    #     render = blender_module.DTMViewerRenderContext(self, 'C:\\Users\\Andrew\\Desktop\\DEMs\\DTEED_020492_1830_021481_1830_A01.IMG','1080p', False, True)
    #     world = bpy.context.scene.world
    #     mist = bpy.context.scene.world.mist_settings
    #
    #     #Before mist is created
    #     #testing background colors
    #     [r, g, b] = world.zenith_color
    #     self.assertNotAlmostEqual(r, 0.040)
    #     self.assertNotAlmostEqual(g, 0.040)
    #     self.assertNotAlmostEqual(b, 0.040)
    #     self.assertNotEqual(world.use_sky_paper, True)
    #     self.assertNotEqual(world.use_sky_blend, True)
    #     self.assertNotEqual(world.use_sky_real, True)
    #
    #     #testing mist properties
    #     self.assertNotEqual(mist.use_mist, True)
    #     self.assertNotEqual(mist.start, 1.0)
    #     self.assertNotEqual(mist.intensity, 0.15)
    #
    #     render.createMist(self)
    #     #After mist is created
    #     #test to insure all properties are as excepcted
    #     [r, g, b] = world.horizon_color
    #     self.assertAlmostEqual(r, 0.0)
    #     self.assertAlmostEqual(g, 0.0)
    #     self.assertAlmostEqual(b, 0.0)
    #
    #     [r, g, b] = world.zenith_color
    #     self.assertAlmostEqual(r, 0.040)
    #     self.assertAlmostEqual(g, 0.040)
    #     self.assertAlmostEqual(b, 0.040)
    #     self.assertEqual(world.use_sky_paper, True)
    #     self.assertEqual(world.use_sky_blend, True)
    #     self.assertEqual(world.use_sky_real, True)
    #
    #     #testing mist properties
    #     self.assertEqual(mist.use_mist, True)
    #     self.assertEqual(mist.start, 1.0)
    #     self.assertEqual(mist.intensity, 0.15)
    #
    #     TestBlender.cleanup(self)

    def cleanup(self):
        world = bpy.context.scene.world
        world.horizon_color = (0.051, 0.051, 0.051)
        world.zenith_color = (0.01, 0.01, 0.01)
        world.ambient_color = (0.0, 0.0, 0.0)
        world.use_sky_paper = False
        world.use_sky_blend = False
        world.use_sky_real = False

        world.mist_settings.use_mist = False
        world.mist_settings.start = 5.0
        world.mist_settings.depth = 25.0
        world.mist_settings.height = 0.0
        world.mist_settings.intensity = 0.0

        world.star_settings.use_stars = False
        world.star_settings.size = 2.0
        world.star_settings.distance_min = 0.0
        world.star_settings.color_random = 0.0
        world.star_settings.average_separation = 15.0


# class TestBlenderLoad(unittest.TestCase):
#     #Test that the file is saving under normal operations
#     #Verify that a file saving directory is generated as expected
#     def test_saving(self):
#         pass
#
#     #In this case, It wasn't to make sure that if the saving operation fails
#     #That the DEM image is in fact loaded
#     def test_saving_fail(self):
#         pass
#
#     #Test to insure the loading logic
#     #Approach
#     #1.) Clear scene
#     #2.) Force image to load with expected data
#     #3.) Test to see if there is a mesh in the scene
#     #4.) Clear scene
#     def test_dtm_loading(self):
#         pass
#
#     def test_dtm_loading_with_null_image(self):
#         pass
#
#     def find_image(self):
#         pass