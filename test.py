#################################################################
###Current functions ported over to their respective modules.####
###File in place for future function development.################
#################################################################
import bpy


def make_camera(point, target_point):
    camera_object = B.Object.New('Camera')
    camera_data = B.Camera.New('view')
    camera_object.link(camera_data)
    scene.link(camera_object)
    camera_object.loc = point
    return
