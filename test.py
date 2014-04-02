#################################################################
###Current functions ported over to their respective modules.####
###File in place for future function development.################
#################################################################
import bpy


def make_camera(point, target_point):
    #Creat both the camera and target.
    bpy.ops.object.camera_add(view_align=False, enter_editmode=False, location=point)
    bpy.ops.object.add(type='EMPTY')
    #Place the empty object variable as camera_target.
    for item in bpy.data.objects:
        if item.type == 'EMPTY':
            camera_target = item
    #Place the camera object variable as camera
    for item in bpy.data.objects:
        if item.type == 'CAMERA':
            camera = item
    #Setting up the camera targets name and location.
    camera_target.name = 'CameraTarget'
    camera_target.location = target_point
    #Setting up the constraint on the camera.
    camera.select = True
    track_constraint = camera.constraints.new('TRACK_TO')
    track_constraint.target = camera_target
    track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
    track_constraint.up_axis = 'UP_Y'

    attach_camera_to_path()
    add_target_to_path()
    return


def attach_camera_to_path():
    deselect_objects()
    for item in bpy.data.objects:
        if item.type == 'CAMERA':
            camera = item
    for item in bpy.data.objects:
        if item.type == 'CURVE':
            curve = item
    camera.select = True
    curve.select = True
    bpy.context.scene.objects.active = curve
    bpy.ops.object.parent_set(type='FOLLOW')
    return


def add_target_to_path():
    deselect_objects()
    for item in bpy.data.objects:
        if item.type == 'EMPTY':
            camera_target = item
    for item in bpy.data.objects:
        if item.type == 'CURVE':
            curve = item
    camera_target.select = True
    curve.select = True
    bpy.ops.object.parent_set(type='FOLLOW')
    return

#Deselection of objects.
def deselect_objects():
    for item in bpy.data.objects:
        item.select = False
    return
