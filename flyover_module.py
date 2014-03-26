__author__ = 'andrewcarter'

import bpy
from bpy.props import *
from mathutils import Vector

class FlyoverDriver( object ):
    #set some default properties for our flyover
    def __init__(self, dem_vector, min_vertex, max_vertex, cycles=1, frames=72):
        for camera in filter(lambda o: o.type == 'CAMERA', bpy.data.objects):
            pass

        #set the proper length
        for scene in bpy.data.scenes:
            scene.camera = camera
            scene.frame_end = cycles*frames

        for camera_target in filter(lambda o: o.name == "CameraTarget", bpy.data.objects):
            pass

        self.camera_target = camera_target
        self.camera = camera #grab the active camera
        self.total_frames = cycles*frames # save length
        self.vector = dem_vector
        self.min_vertex = min_vertex
        self.max_vertex = max_vertex

    #Creates a circular path around the whole dem the camera tracks the
    #center of the DEM
    def circle_pattern(self):
        # Add a circular path that dicatates the camera path
        bpy.ops.curve.primitive_bezier_circle_add()
        circle = bpy.context.object
        circle.location = (self.camera_target.location[0], self.camera_target.location[1], self.camera_target.location[2]+5)
        radius = min(self.vector[0], self.vector[1])/2
        circle.scale = (radius, radius, 1.0)
        co = circle.data.splines[0].bezier_points[-1].co
        self.camera.location = co

        self.camera.select = True
        bpy.ops.object.parent_set(type='FOLLOW')
        track_constraint = self.camera.constraints.new('TRACK_TO')
        track_constraint.target = self.camera_target
        track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        track_constraint.up_axis = 'UP_Y'
        return

    def oval_pattern(self):
        p1 = p5 = Vector(self.min_vertex[0] + self.vector[0]/2, self.min_vertex[1], self.max_vertex[2]+5)
        p2 = Vector(self.min_vertex[0], self.min_vertex[1] + self.vector[1]/2, self.max_vertex[2]+5)
        p3 = Vector(self.min_vertex[0] + self.vector[0]/2, self.max_vertex[1], self.max_vertex[2]+5)
        p4 = Vector(self.max_vertex[0], self.min_vertex[1] + self.vector[1]/2, self.max_vertex[2]+5)

        coordinate_list = [p1, p2, p3, p4, p5]

        curve = bpy.data.curves.new(name='Curve', type='CURVE')
        curve.dimensions = '3D'

        oval = bpy.data.objects.new("ObjCurve", curve)
        oval.location = (self.camera_target.location[0], self.camera_target.location[1], self.camera_target.location[2]+5)
        bpy.context.scene.objects.link(oval)

        poly = curve.splines.new('POLY')
        poly.points.add(len(coordinate_list)-1)
        for num in range(len(coordinate_list)):
            x, y, z = coordinate_list[num]
            poly.points[num].co = (x, y, z, 1)

        return

    def hourglass_pattern(self):
        return

    def linear_pattern(self):
        return

    def diamond_pattern(self):
        #build path
        p1 = Vector((self.min_vertex[0] + self.vector[0]/2, self.min_vertex[1]+2, self.max_vertex[2]+5))
        p2 = Vector((self.min_vertex[0]+2, self.min_vertex[1] + self.vector[1]/2, self.max_vertex[2]+5))
        p3 = Vector((self.min_vertex[0] + self.vector[0]/2, self.max_vertex[1]-2, self.max_vertex[2]+5))
        p4 = Vector((self.max_vertex[0]-2, self.min_vertex[1] + self.vector[1]/2, self.max_vertex[2]+5))
        coordinate_list = [p1, p2, p3, p4, p1]

        curve = bpy.data.curves.new(name='Curve', type='CURVE')
        curve.dimensions = '3D'

        diamond = bpy.data.objects.new("DiamondPath", curve)
        diamond.location = Vector((0, 0, 5))
        bpy.context.scene.objects.link(diamond)

        poly = curve.splines.new('POLY')
        poly.points.add(len(coordinate_list)-1)
        for num in range(len(coordinate_list)):
            x, y, z = coordinate_list[num]
            poly.points[num].co = (x, y, z, 1)
        self.camera.location = p1

        self.camera.select = True
        bpy.ops.object.parent_set(type='FOLLOW')
        track_constraint = self.camera.constraints.new('TRACK_TO')
        track_constraint.target = self.camera_target
        track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        track_constraint.up_axis = 'UP_Y'

        return