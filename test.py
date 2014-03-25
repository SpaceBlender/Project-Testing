import bpy
import math


#Simple test to ensure that import is good.
#Will be gotten rid when implementing functions into flyover.
def test_func():
    print("Import good!")


#Helper function to get the distance between two functions.
def distance_two_points(point_one, point_two):
    distance = math.sqrt((point_one[0] - point_two[0])*(point_one[0] - point_two[0]) + (point_one[1] - point_two[1])*(point_one[1] - point_two[1]) + (point_one[2] - point_two[2])*(point_one[2] - point_two[2]))
    return distance


#Helper function to find the midpoint between two points.
def midpoint_two_points(point_one, point_two):
    return (point_one[0]+point_two[0])/2, (point_one[1]+point_two[1])/2, (point_one[2]+point_two[2])/2

#Function to get a simple liner path for the overall DEM MESH.
#Gets the path by calculating the midpoints in the DEM image and makes the path run through the long ways of the DEM.
def get_liner_path():
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
    #List holders for work to be done.
    #Holds the midpoints we are going to work with.
    midpoint_holder = []
    #Our return list of the values to be returned from this function.
    return_list = []
    #Getting a new height value to be used for the path.
    #May change to a parameter later to be dynamic.
    z_max_value += 0.5
    #If statement to see which way is longer.
    #Helps us find out which way the path will run.
    if distance_two_points(x_min_point, y_max_point) > distance_two_points(x_min_point, y_min_point):
        midpoint_holder.append(midpoint_two_points(x_min_point, y_min_point))
        midpoint_holder.append(midpoint_two_points(x_max_point, y_max_point))
    else:
        midpoint_holder.append(midpoint_two_points(x_min_point, y_max_point))
        midpoint_holder.append(midpoint_two_points(x_max_point, y_min_point))
    #Loop to give us our new points to be returned.
    for point in midpoint_holder:
        new_point = (point[0], point[1], z_max_value)
        return_list.append(new_point)
    #Final return of get liner path function.
    return return_list


#Creates a poly path out of N points.
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
        if(index == 0):
            #First iteration gives or holder the value of the curve origin.
            o_x, o_y, o_z = points[index]
        else:
            #Because the origin of the curve is different from (0, 0, 0),
            #we need to change the following points relative to our curve origin.
            #As if our curve origin is (0, 0, 0).
            x, y, z = points[index]
            polyline.points[index].co = ((x - o_x), (y - o_y), z, 1)
