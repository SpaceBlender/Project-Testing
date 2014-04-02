import bpy
import math
from bpy.props import *
from mathutils import Vector


class FlyoverDriver(object):
    #Class constructor.
    def __init__(self):
        #Changed this module to be modular.
        #Meaning we can call all the functions here without having to worry about class initialization.
        #Can be useful for users who don't want to run the entire plug-in again to get different fly paths.
        #Can also be useful for other meshes to create flyovers.
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
    #Gets the path by calculating the midpoints in the DEM image and...
    #...makes the path run through the long ways of the DEM.
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
        if FlyoverDriver.distance_two_points(x_min_point, y_max_point) > FlyoverDriver.distance_two_points(x_min_point,
                                                                                                           y_min_point):
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