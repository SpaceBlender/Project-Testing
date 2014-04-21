__author__ = 'Andrew'
from . import blender_module
import bpy
import unittest
import bpy.props

#The DEM you want to use for blender unit tests
dem = 'C:\\Users\\Andrew\\Desktop\\DEMs\\DTEED_020492_1830_021481_1830_A01.IMG'

#This class of tests focuses on the DTMViewrRenderContext
#It tests the newly coded stars and mist functions
class TestBlenderDTMViewerRenderContext(unittest.TestCase):
    def test_stars(self):
        world = bpy.context.scene.world
        render = blender_module.DTMViewerRenderContext(dem,'1080p',True, False)

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

    def test_mist(self):
        _DTMViewerRenderContext = blender_module.DTMViewerRenderContext(dem,'1080p', False, True)
        world = bpy.context.scene.world
        mist = bpy.context.scene.world.mist_settings

        #Before mist is created
        #testing background colors
        [r, g, b] = world.zenith_color
        self.assertNotAlmostEqual(r, 0.040)
        self.assertNotAlmostEqual(g, 0.040)
        self.assertNotAlmostEqual(b, 0.040)
        self.assertNotEqual(world.use_sky_paper, True)
        self.assertNotEqual(world.use_sky_blend, True)
        self.assertNotEqual(world.use_sky_real, True)

        #testing mist properties
        self.assertNotEqual(mist.use_mist, True)
        self.assertNotEqual(mist.start, 1.0)

        _DTMViewerRenderContext.createMist(_DTMViewerRenderContext)
        #After mist is created
        #test to insure all properties are as excepcted
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

        #testing mist properties
        self.assertEqual(mist.use_mist, True)
        self.assertEqual(mist.start, 1.0)
        self.assertAlmostEqual(mist.intensity, 0.15)

        TestBlenderDTMViewerRenderContext.cleanup(self)

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


#This whole class of tests is dedicated to insuring our newly coded loader function is working correctly.
#The tests that it covers are focused on saving and dtm loading.
class TestBlenderLoad(unittest.TestCase):
    #This is a very simple test to insure that a mesh is being created
    #We assume that the mesh logic is correct, so we are not testing to see if the DTM for correctness
    #Only that it exists
    def test_dtm_loading(self):
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
        self.assertTrue(TestBlenderLoad.find_image(self))
        blender_module.DTMViewerRenderContext.clearScene(self)


    # This test insures that if a bad file path is given that the process fails out and
    # no image is loaded
    def test_dtm_loading_with_null_image(self):
        blender_module.DTMViewerRenderContext.clearScene(self)
        blender_module.load(self, None,
            filepath='',
            scale=0.01,
            bin_mode='BIN12-FAST',
            color_pattern='None',
            flyover_pattern='No flyover',
            texture_location=None,
            cropVars=False,
            resolution='1080p',
            stars=False,
            mist=False)
        self.assertFalse(TestBlenderLoad.find_image(self))
        blender_module.DTMViewerRenderContext.clearScene(self)


    def find_image(self):
        for item in bpy.data.objects:
            if (item.type == 'MESH'):
                return True
        return False