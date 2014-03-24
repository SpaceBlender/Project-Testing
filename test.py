import bpy
import math


def test_func():
    print("Import good!")


def get_liner_path():
    temp = None
    line_counter = 0
    line_length = 0
    holder = 0
    temp_count = 0
    vertex_list = []
    for item in bpy.data.objects:
        #print(item.name)
        if item.type == 'MESH':
            for vertex in item.data.vertices:
                if temp is None:
                    pass
                elif line_length > 0:
                    if line_length/2 == line_counter % line_length:
                        #print(vertex.co)
                        #print(line_length/2)
                        #print(line_counter)
                        vertex_list.append(vertex.co)
                else:
                    distance = math.sqrt((temp.x - vertex.co.x)*(temp.x - vertex.co.x) + (temp.y - vertex.co.y)*(temp.y - vertex.co.y) + (temp.z - vertex.co.z)*(temp.z - vertex.co.z))
                    if distance > holder:
                        holder = distance
                    if distance > 1:
                        temp_count += 1
                        line_length = line_counter
                    #first = vertex.co.y
                    #if first < 0:
                    #    first = -1 * first
                    #second = temp.y
                    #if second < 0:
                    #    second = -1* second
                    #check = first - second
                    #if holder < check:
                    #    holder = check
                    #if check > 1:
                    #    line_length = line_counter
                    #old stuff.
                line_counter += 1
                temp = vertex.co
    output_list = []
    print(line_counter)
    print(line_length)
    print(holder)
    print(temp_count)
    for vertex in vertex_list:
        point = (vertex.x, vertex.y, vertex.z + .5)
        output_list.append(point)
    return output_list


def make_path(object_name, curve_name, points):
    curve_data = bpy.data.curves.new(name=curve_name, type='CURVE')
    curve_data.dimensions = '3D'
    object_data = bpy.data.objects.new(object_name, curve_data)
    #starting point
    object_data.location = points[0]
    bpy.context.scene.objects.link(object_data)
    #smooth curve
    polyline = curve_data.splines.new('POLY')
    polyline.points.add(len(points)-1)
    for index in range(len(points)):
        if(index == 0):
            pass
        else:
            x, y, z = points[index]
            polyline.points[index].co = (x, y, z, 1)
            #polyline.order_u = len(polyline.points) - 1
            #polyline.use_endpoint_u = True