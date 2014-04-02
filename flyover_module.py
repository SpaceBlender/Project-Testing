import bpy
import math
from bpy.props import *
from mathutils import Vector
import math

class FlyoverDriver(object):
    #set some default properties for our flyover
    def __init__(self):
        mesh = bpy.data.objects[0] #our DEM is the first object in the list
        x = tuple(map(lambda xyz: xyz[0], mesh.bound_box))
        y = tuple(map(lambda xyz: xyz[1], mesh.bound_box))
        z = tuple(map(lambda xyz: xyz[2], mesh.bound_box))
        self.min_v = (min(x), min(y), min(z))
        self.max_v = (max(x), max(y), max(z))
        self.vector = tuple(map(lambda a, b: abs(a - b), self.min_v, self.max_v))
        self.center = (self.min_v[0]+self.vector[0]/2, self.min_v[1]+self.vector[1]/2, self.min_v[2]+self.vector[2]/2)

    #################################################################################################################
    ########################################## HELPER FUNCTIONS #####################################################
    # Adds the Empty target for the camera to track
    def add_target(self, location):
        bpy.ops.object.add(type='EMPTY')
        camera_target = bpy.context.object #select new object
        camera_target.name = 'CameraTarget'
        camera_target.location = location
        return camera_target

    #Create a camera set to a specific location
    def add_camera(self, location, frames=72):
        # Create a new default camera
        bpy.ops.object.camera_add()
        camera = bpy.data.objects['Camera']
        #Set camera location and name
        camera.location = location
        camera.name = "Camera"
        camera.data.clip_end = 500.0
        #set scene camera
        scene = bpy.data.scenes[0] #we only have one scene in this context
        scene.camera = camera
        scene.frame_end = frames

        return camera

    def attach_camera(self, starting_point, curve, camera):
        camera.location = starting_point

        path_constraint = camera.constraints.new('FOLLOW_PATH')
        path_constraint.target = curve
        path_constraint.forward_axis = 'TRACK_NEGATIVE_Y'
        path_constraint.up_axis = 'UP_Y'
        path_constraint.use_curve_follow = True

        #necessary for setting the camera to the path
        bpy.ops.object.select_all(action="DESELECT")
        camera.select = True
        curve.select = True
        bpy.context.scene.objects.active = curve
        bpy.ops.object.parent_set(type='FOLLOW')

    def set_target(self, camera, camera_target):
        track_constraint = camera.constraints.new('TRACK_TO')
        track_constraint.target = camera_target
        track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        track_constraint.up_axis = 'UP_Y'
    ##################################################################################################################

    # Setup a camera to track our empty target
    def no_flyover(self):
        xy_distance = math.sqrt(self.vector[0] ** 2 + self.vector[1] ** 2)
        location = (self.min_v[0], self.min_v[1], self.center[2]+xy_distance*0.33)

        camera = FlyoverDriver.add_camera(self, location)
        camera_target = FlyoverDriver.add_target(self, self.center)

        camera.select = True
        FlyoverDriver.set_target(camera, camera_target)

    #Creates a circular path around the whole dem the camera tracks the
    #center of the DEM
    def circle_pattern(self):
        camera = FlyoverDriver.add_camera(self, self.center)
        camera_target = FlyoverDriver.add_target(self, self.center)

        # Add a circular path that dictates the camera path
        bpy.ops.curve.primitive_bezier_circle_add()
        circle = bpy.data.objects['BezierCircle']
        circle.location = (self.center[0], self.center[1], self.center[2]+5)
        radius = min(self.vector[0], self.vector[1])/2
        circle.scale = (radius, radius, 1.0) #scale circle
        co = tuple(map(lambda a, b: a - b, camera.location, (radius, 0, 0)))

        FlyoverDriver.attach_camera(self, co, circle, camera)
        FlyoverDriver.set_target(self, camera, camera_target)

        return

    def oval_pattern(self):
        return

    def diamond_pattern(self):
        camera = FlyoverDriver.add_camera(self, self.center)
        camera_target = FlyoverDriver.add_target(self, self.center)

        #build path
        p1 = (0, self.vector[1]/2, self.vector[2]+5)
        p2 = (self.vector[0]/2, self.vector[1], self.vector[2]+5)
        p3 = (self.vector[0], self.vector[1]/2, self.vector[2]+5)
        p4 = (self.vector[0]/2, 0, self.vector[2]+5)
        coordinate_list = [p1, p2, p3, p4, p1]

        diamond = FlyoverDriver.make_path("DiamondPath", "DiamondPath", coordinate_list)
        FlyoverDriver.attach_camera(self, p4, diamond, camera)
        FlyoverDriver.set_target(self, camera, camera_target)
        return

    def hourglass_pattern(self):
        return

    #Liner Function itself. Calls helper functions in under Liner Helper Functions.
    @staticmethod
    def linear_pattern():
        list_holder = FlyoverDriver.get_liner_path()
        list_holder = FlyoverDriver.check_height(list_holder)
        FlyoverDriver.make_path("Curve", "Linear", list_holder)
        return

    #############################################################
    ###########Check Height Helper Function#######################
    #############################################################
    @staticmethod
    def check_height(input_list):
        #Prep list of vertices in which are the closest points in the mesh from our input..
        prep_list = []
        #Set the same number of vertices as our input list.
        for item in input_list:
            prep_list.append((item[0], item[1], item[2]))
        #Holder list to check the overall distance of a vertex in the mesh from the input lists vertex.
        holder_list = []
        #Setting up our holder list to start comparing distances to the appropriate index.
        for item in input_list:
            holder_list.append(100)
        #Run through each object to find the MESH.
        for item in bpy.data.objects:
            if item.type == 'MESH':
                #Run through each vertex to get our data.
                for vertex in item.data.vertices:
                    #Check each vertex in our input list against each vertex in the mesh.
                    for input_index, input_vertex in enumerate(input_list):
                        #New point to input into our distance calculation.
                        vertex_point = (vertex.co.x, vertex.co.y, vertex.co.z)
                        #Calculating the distance between our input list point and the mesh vertex point.
                        #Optimize later if able to.
                        distance = FlyoverDriver.distance_two_points(input_vertex, vertex_point)
                        #Compare our distance and the holders value.
                        if distance < holder_list[input_index]:
                            #If the new distance is closer then we can update our temp variables.
                            holder_list[input_index] = distance
                            prep_list[input_index] = (vertex.co.x, vertex.co.y, vertex.co.z)
        #Setting up our return list.
        return_list = []
        #Get the values from our prep list and place them into our final return list.
        for item in prep_list:
            #Here is where we get the increase in the z access for every point.
            point = (item[0], item[1], item[2] + 2.5)
            return_list.append(point)
        return return_list

    #############################################################
    ###########Make Path Helper Function#########################
    #############################################################
    #Creates a poly path out of N points.
    @staticmethod
    def make_path(object_name, curve_name, points):
        #Sets up or curve and object to be added to the scene.
        curve_data = bpy.data.curves.new(name=curve_name, type='CURVE')
        curve_data.dimensions = '3D'
        object_data = bpy.data.objects.new(object_name, curve_data)
        #Starting point of our curve. The first point in our input list.
        object_data.location = points[0]
        bpy.context.scene.objects.link(object_data)
        #Type of curve, POLY, and the number of points to be added.
        polyline = curve_data.splines.new('POLY')
        polyline.points.add(len(points)-1)
        #Need a holder for our origin.
        o_x, o_y, o_z = (0, 0, 0)
        for index in range(len(points)):
            if index == 0:
                #First iteration gives or holder the value of the curve origin.
                o_x, o_y, o_z = points[index]
            else:
                #Because the origin of the curve is different from (0, 0, 0),
                #we need to change the following points relative to our curve origin.
                #As if our curve origin is (0, 0, 0).
                x, y, z = points[index]
                polyline.points[index].co = ((x - o_x), (y - o_y), (z - o_z), 1)

        return object_data

    #############################################################
    ###########General Helper Functions###########################
    #############################################################
    #Helper function to get the distance between two functions.
    @staticmethod
    def distance_two_points(point_one, point_two):
        distance = math.sqrt((point_one[0] - point_two[0])*(point_one[0] - point_two[0]) +
                             (point_one[1] - point_two[1])*(point_one[1] - point_two[1]) +
                             (point_one[2] - point_two[2])*(point_one[2] - point_two[2]))
        return distance

    #Helper function to find the midpoint between two points.
    @staticmethod
    def midpoint_two_points(point_one, point_two):
        return (point_one[0]+point_two[0])/2, (point_one[1]+point_two[1])/2, (point_one[2]+point_two[2])/2

    #Helper function to get the boundaries of the DEM.
    @staticmethod
    def get_dem_boundaries():
        #Simple value holders for getting our corners and highest point in the DEM.
        #Farthest NW corner of the DEM.
        x_max_point = (0, 0, 0)
        #Farthest SE corner of the DEM.
        x_min_point = (100, 0, 0)
        #Farthest NE corner of the DEM.
        y_max_point = (0, 0, 0)
        #Farthest SW corner of the DEM.
        y_min_point = (0, 100, 0)
        #Max height value of the DEM.
        z_max_value = -10
        #Return List
        return_list = []
        #Run through each object to find the MESH.
        for item in bpy.data.objects:
            if item.type == 'MESH':
                #Run through each vertex to get our data.
                for vertex in item.data.vertices:
                    #Series of if statements to get the correct values for our value holders.
                    if vertex.co.x >= x_max_point[0]:
                        x_max_point = (vertex.co.x, vertex.co.y, vertex.co.z)
                    if vertex.co.x < x_min_point[0]:
                        x_min_point = (vertex.co.x, vertex.co.y, vertex.co.z)
                    if vertex.co.y >= y_max_point[1]:
                        y_max_point = (vertex.co.x, vertex.co.y, vertex.co.z)
                    if vertex.co.y < y_min_point[1]:
                        y_min_point = (vertex.co.x, vertex.co.y, vertex.co.z)
                    if vertex.co.z > z_max_value:
                        z_max_value = vertex.co.z
        return_list.append(x_max_point)
        return_list.append(x_min_point)
        return_list.append(y_max_point)
        return_list.append(y_min_point)
        return_list.append(z_max_value)
        return return_list

    #############################################################
    ###########Liner Helper Functions############################
    #############################################################
    #Function to get a simple liner path for the overall DEM MESH.
    #Gets the path by calculating the midpoints in the DEM image and makes the path run through the long ways of the DEM.
    @staticmethod
    def get_liner_path():
        boundaries_list = FlyoverDriver.get_dem_boundaries()
        x_max_point = boundaries_list[0]
        #Farthest SE corner of the DEM.
        x_min_point = boundaries_list[1]
        #Farthest NE corner of the DEM.
        y_max_point = boundaries_list[2]
        #Farthest SW corner of the DEM.
        y_min_point = boundaries_list[3]
        #List holders for work to be done.
        #Holds the midpoints we are going to work with.
        midpoint_holder = []
        #Our return list of the values to be returned from this function.
        return_list = []
        #If statement to see which way is longer.
        #Helps us find out which way the path will run.
        if FlyoverDriver.distance_two_points(x_min_point, y_max_point) > FlyoverDriver.distance_two_points(x_min_point, y_min_point):
            midpoint_holder.append(FlyoverDriver.midpoint_two_points(x_min_point, y_min_point))
            midpoint_holder.append(FlyoverDriver.midpoint_two_points(x_max_point, y_max_point))
        else:
            midpoint_holder.append(FlyoverDriver.midpoint_two_points(x_min_point, y_max_point))
            midpoint_holder.append(FlyoverDriver.midpoint_two_points(x_max_point, y_min_point))
        #Loop to give us our new points to be returned.
        for point in midpoint_holder:
            new_point = (point[0], point[1], point[2])
            return_list.append(new_point)
        #Final return of get liner path function.
        return return_list