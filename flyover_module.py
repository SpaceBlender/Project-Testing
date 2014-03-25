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

    #Creates a circular path around the whole dem the camera tracks the
    #center of the DEM
    def circle_flyover_pattern(self):
        # Add a circular path that dicatates the camera path
        bpy.ops.curve.primitive_bezier_circle_add()
        circle = bpy.context.object
        distance = math.sqrt(self.vector[0] **2 + self.vector[1] **2)
        circle.location = (self.camera_target.location[0], self.camera_target.location[1], self.camera_target.location[2]+10)

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


        # bpy.ops.object.parent_set(type='FOLLOW_PATH')
        # constraint_path = self.camera.constraints.new('FOLLOW')
        # constraint_path.target = self.camera.location
        # constraint_path.forward_axis = 'TRACK_NEGATIVE_Z'
        # constraint_path.up_axis = 'UP_Y'

        return
