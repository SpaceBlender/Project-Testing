__author__ = 'andrewcarter'

import bpy
from bpy.props import *

class flyover_driver( object ):
    #set some default properties for our flyover
    def __init__(self, cycles=1, frames=72):
        for camera in filter(lambda o: o.type == 'CAMERA', bpy.data.objects):
            pass

        #set the proper length
        for scene in bpy.data.scenes:
            scene.camera = camera
            scene.frame_end = cycles*frames

        for camera_target in filter(
                lambda o: o.name == "CameraTarget",
                bpy.data.objects
        ):
            pass

        self.camera_target = camera_target
        self.camera = camera #grab the active camera
        self.total_frames = cycles*frames # save length
        print ("Camera: " + camera)
        print ("Camera Target: " + camera_target)
        print ("Total Frames: " + total_frames)


    #Creates a circular path around the whole dem the camera tracks the
    #center of the DEM
    def circleFlyoverPattern(self):
        # Add a circular path that dicatates the camera path
        bpy.ops.curve.primitive_bezier_circle_add()
        bpy.ops.object.parent_set(type='FOLLOW')
        for o in filter(lambda o: o.type == 'CURVE', bpy.data.objects):
            crv = o
        for o in bpy.data.curves:
            o.path_duration = self.total_frames
        crv.name = 'CirclePath'
        for o in crv.children:
            o.path_duration = self.total_frames
        camera_path = crv

        #construct path and tracking
        bpy.ops.object.select_pattern(pattern=self.camera.name)
        bpy.ops.object.constraint_add(type='FOLLOW_PATH')
        bpy.ops.object.constraint_add(type='TRACK_TO')
        for constraint in self.camera.constraints:
            # always watch the camera target
            if constraint.type == 'TRACK_TO':
                constraint.target = self.camera_target
                constraint.track_axis = 'TRACK_NEGATIVE_Z'
                constraint.up_axis = 'UP_Y'
            # always stay 100 units away from the target
            if constraint.type == 'FOLLOW_PATH':
                constraint.target = camera_path
                constraint.forward_axis = 'TRACK_NEGATIVE_Z'
                constraint.up_axis = 'UP_Y'
                self.__cameraPathConstraint = constraint