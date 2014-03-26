__author__ = 'andrewcarter'

import bpy
from bpy.props import *
import math

class FlyoverDriver( object ):
    #set some default properties for our flyover
    def __init__(self, dem_vector, cycles=1, frames=72):
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
        print("Camera: ", self.camera)
        print("Camera Location: ", self.camera.location)
        print("My Vector: ", dem_vector)

    #Creates a circular path around the whole dem the camera tracks the
    #center of the DEM
    def circle_pattern(self):
        # Add a circular path that dicatates the camera path
        bpy.ops.curve.primitive_bezier_circle_add()
        circle = bpy.context.object
        circle.location = (self.camera_target.location[0], self.camera_target.location[1], self.camera_target.location[2]+3)
        radius = min(self.vector[0], self.vector[1])/2
        circle.scale = (radius, radius, 1.0)
        co = circle.data.splines[0].bezier_points[-1].co
        self.camera.location = tuple(map(lambda a, b: a + b, co, ))

        print("Where is my camera? ", self.camera.location)

        self.camera.select = True
        bpy.ops.object.parent_set(type='FOLLOW')
        track_constraint = self.camera.constraints.new('TRACK_TO')
        track_constraint.target = self.camera_target
        track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        track_constraint.up_axis = 'UP_Y'
        return

    def oval_pattern(self):
        return

    def hourglass_pattern(self):
        return

    def linear_pattern(self):
        return

    def diamond_pattern(self):
        return