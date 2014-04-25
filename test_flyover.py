__author__ = "Andrew"

from . import flyover_module
import unittest
import os
import math

class TestFlyoverPatterns(unittest.TestCase):
    def test_no_flyover(self):
        pass

    def test_linnear_pattern(self):
        pass

    def test_diamond_pattern(self):
        pass

    def test_circle_pattern(self):
        pass

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

    def get_dem_boundaries(self):
        pass

