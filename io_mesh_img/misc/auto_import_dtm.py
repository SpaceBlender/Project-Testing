# ##### BEGIN GPL LICENSE BLOCK #####
#
#	This program is free software; you can redistribute it and/or
#	modify it under the terms of the GNU General Public License
#	as published by the Free Software Foundation; either version 2
#	of the License, or (at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program; if not, write to the Free Software Foundation,
#	Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# USAGE:
#
#   Blender seems to have no way of passing arguments to a command line
#   script so this script keys off of the environment variables:
#       DTM_IMG - path to the DTM in .IMG format
#       DTM_TEXTURE - path to the file to drape over the DTM
#	DTM_BLEND - path save the resulting .blend file
#
#   Once these values are set, you can simple call blender as:
#       % blender -P ./auto_import_dtm.py
#
#   Adding -b tells blender not to display a GUI and simply exit:
#       % blender -b -P ./auto_import_dtm.py
#
#   A full usage example (assuming a bash shell):
#       %
#       % export DTM_BLEND=/home/tims/DTEEC_1_2_3.blend
#       % export DTM_IMG=/home/tims/DTEEC_1_2_3.IMG
#       % export DTM_TEXTURE=/home/tims/DTEEC_1_2_3.br.jpg
#       % blender -b -P ./auto_import_dtm.py
#       %

from struct import pack, unpack, unpack_from
import queue, threading

import bpy
from bpy.ops import *
import os
import math

def encap_1(val):
	''' blender 2.5x uses [val] while 2.6x uses val -- this helps ease that '''
	if bpy.app.version[0] >= 2 and bpy.app.version[1] < 60:
		return [val]
	return val

class image_properties:
	''' keeps track of image attributes throughout the hirise_dtm_importer class '''
	def __init__(self, name, dimensions, pixel_scale):
		self.name( name )
		self.dims( dimensions )
		self.processed_dims( dimensions )
		self.pixel_scale( pixel_scale )

	def dims(self, dims=None):
		if dims is not None:
			self.__dims = dims
		return self.__dims

	def processed_dims(self, processed_dims=None):
		if processed_dims is not None:
			self.__processed_dims = processed_dims
		return self.__processed_dims

	def name(self, name=None):
		if name is not None:
			self.__name = name
		return self.__name

	def pixel_scale(self, pixel_scale=None):
		if pixel_scale is not None:
			self.__pixel_scale = pixel_scale
		return self.__pixel_scale

class hirise_dtm_importer(object):
	''' methods to understand/import a HiRISE DTM formatted as a PDS .IMG '''

	def __init__(self, filepath):
		self.__filepath = filepath
		self.__ignore_value = 0x00000000
		self.__bin_mode = 'BIN6'
		self.scale( 1.0 )
		self.__cropXY = False

	def bin_mode(self, bin_mode=None):
		if bin_mode != None:
			self.__bin_mode = bin_mode
		return self.__bin_mode

	def scale(self, scale=None):
		if scale is not None:
			self.__scale = scale
		return self.__scale

	def crop(self, widthX, widthY, offX, offY):
		self.__cropXY = [ widthX, widthY, offX, offY ]
		return self.__cropXY

	############################################################################
	## PDS Label Operations
	############################################################################

	def parsePDSLabel(self, labelIter, currentObjectName=None, level = ""):
		# Let's parse this thing... semi-recursively
		## I started writing this caring about everything in the PDS standard but ...
		## it's a mess and I only need a few things -- thar be hacks below
		## Mostly I just don't care about continued data from previous lines
		label_structure = []

		# When are we done with this level?
		endStr = "END"
		if not currentObjectName is None:
			endStr = "END_OBJECT = %s" % currentObjectName
		line = ""

		while not line.rstrip() == endStr:
			line = next(labelIter)

			# Get rid of comments
			comment = line.find("/*")
			if comment > -1:
				line = line[:comment]

			# Take notice of objects
			if line[:8] == "OBJECT =":
				objName = line[8:].rstrip()
				label_structure.append(
					(
					 objName.lstrip().rstrip(),
					 self.parsePDSLabel(labelIter, objName.lstrip().rstrip(), level + "	")
					)
				)
			elif line.find("END_OBJECT =") > -1:
				pass
			elif len(line.rstrip().lstrip()) > 0:
				key_val = line.split(" = ", 2)
				if len(key_val) == 2:
					label_structure.append( (key_val[0].rstrip().lstrip(), key_val[1].rstrip().lstrip()) )

		return label_structure

	# There has got to be a better way in python?
	def iterArr(self, label):
		for line in label:
			yield line

	def getPDSLabel(self, img):
		# Just takes file and stores it into an array for later use
		label = []
		done = False;
		# Grab label into array of lines
		while not done:
			line = str(img.readline(), 'utf-8')
			if line.rstrip() == "END":
				done = True
			label.append(line)
		return (label, self.parsePDSLabel(self.iterArr(label)))

	def getLinesAndSamples(self, label):
		''' uses the parsed PDS Label to get the LINES and LINE_SAMPLES parameters
				from the first object named "IMAGE" -- is hackish
		'''
		lines = None
		line_samples = None
		for obj in label:
			if obj[0] == "IMAGE":
				return self.getLinesAndSamples(obj[1])
			if obj[0] == "LINES":
				lines = int(obj[1])
			if obj[0] == "LINE_SAMPLES":
				line_samples = int(obj[1])

		return ( line_samples, lines )

	def getValidMinMax(self, label):
		''' uses the parsed PDS Label to get the VALID_MINIMUM and VALID_MAXIMUM parameters
				from the first object named "IMAGE" -- is hackish
		'''
		lines = None
		line_samples = None
		for obj in label:
			if obj[0] == "IMAGE":
				return self.getValidMinMax(obj[1])
			if obj[0] == "VALID_MINIMUM":
				vmin = float(obj[1])
			if obj[0] == "VALID_MAXIMUM":
				vmax = float(obj[1])

		return ( vmin, vmax )

	def getMissingConstant(self, label):
		''' uses the parsed PDS Label to get the MISSING_CONSTANT parameter
				from the first object named "IMAGE" -- is hackish
		'''

		lines = None
		line_samples = None
		for obj in label:
			if obj[0] == "IMAGE":
				return self.getMissingConstant(obj[1])
			if obj[0] == "MISSING_CONSTANT":
				bit_string_repr = obj[1]

		# This is always the same for a HiRISE image, so we are just checking it
		# to be a little less insane here. If someone wants to support another
		# constant then go for it. Just make sure this one continues to work too
		pieces = bit_string_repr.split("#")
		if pieces[0] == "16" and pieces[1] == "FF7FFFFB":
			ignore_value = unpack("f", pack("I", 0xFF7FFFFB))[0]

		return ( ignore_value )

	############################################################################
	## Image operations
	############################################################################

	# decorator to run a generator in a thread
	def threaded_generator(func):
		def start(*args,**kwargs):
			# Setup a queue of returned items
			yield_q = queue.Queue()
			# Thread to run generator inside of
			def worker():
				for obj in func(*args,**kwargs): yield_q.put(obj)
				yield_q.put(StopIteration)
			t = threading.Thread(target=worker)
			t.start()
			# yield from the queue as fast as we can
			obj = yield_q.get()
			while obj is not StopIteration:
				yield obj
				obj = yield_q.get()

		# return the thread-wrapped generator
		return start

	def bin2(self, image_iter, bin2_method_type="SLOW"):
		''' this is an iterator that: Given an image iterator will yield binned lines '''

		ignore_value = self.__ignore_value

		img_props = next(image_iter)
		# dimensions shrink as we remove pixels
		processed_dims = img_props.processed_dims()
		processed_dims = ( processed_dims[0]//2, processed_dims[1]//2 )
		img_props.processed_dims( processed_dims )
		# each pixel is larger as binning gets larger
		pixel_scale = img_props.pixel_scale()
		pixel_scale = ( pixel_scale[0]*2, pixel_scale[1]*2 )
		img_props.pixel_scale( pixel_scale )
		yield img_props

		# Take two lists  [a1, a2, a3], [b1, b2, b3] and combine them into one
		# list of [a1 + b1, a2+b2,  ... ] as long as both values are not ignorable
		combine_fun = lambda a, b: a != ignore_value and b != ignore_value and (a + b)/2 or ignore_value

		line_count = 0
		ret_list = []
		for line in image_iter:
			if line_count == 1:
				line_count = 0
				tmp_list = list(map(combine_fun, line, last_line))
				while len(tmp_list) > 1:
					ret_list.append( combine_fun( tmp_list[0], tmp_list[1] ) )
					del tmp_list[0:2]
				yield ret_list
				ret_list = []
			else:
				last_line = line
				line_count += 1

	def bin6(self, image_iter, bin6_method_type="SLOW"):
		''' this is an iterator that: Given an image iterator will yield binned lines '''

		img_props = next(image_iter)
		# dimensions shrink as we remove pixels
		processed_dims = img_props.processed_dims()
		processed_dims = ( processed_dims[0]//6, processed_dims[1]//6 )
		img_props.processed_dims( processed_dims )
		# each pixel is larger as binning gets larger
		pixel_scale = img_props.pixel_scale()
		pixel_scale = ( pixel_scale[0]*6, pixel_scale[1]*6 )
		img_props.pixel_scale( pixel_scale )
		yield img_props

		if bin6_method_type == "FAST":
			bin6_method = self.bin6_real_fast
		else:
			bin6_method = self.bin6_real

		raw_data = []
		line_count = 0
		for line in image_iter:
			raw_data.append( line )
			line_count += 1
			if line_count == 6:
				yield bin6_method( raw_data )
				line_count = 0
				raw_data = []

	def bin6_real(self, raw_data):
		''' does a 6x6 sample of raw_data and returns a single line of data '''
		# TODO: make this more efficient

		binned_data = []
		IGNORE_VALUE = self.__ignore_value

		base = 0
		for i in range(0, len(raw_data[0])//6):

			ints = (raw_data[0][base : base + 6] +
				raw_data[1][base : base + 6] +
				raw_data[2][base : base + 6] +
				raw_data[3][base : base + 6] +
				raw_data[4][base : base + 6] +
				raw_data[5][base : base + 6] )

			# Filter out those unwanted hugely negative values...
			ints = [num for num in ints if num != IGNORE_VALUE]

			# If we have all pesky values, return a pesky value
			if not ints:
				binned_data.append( IGNORE_VALUE )
			else:
				binned_data.append( sum(ints, 0.0) / len(ints) )

			base += 6

		return binned_data

	def bin6_real_fast(self, raw_data):
		''' takes a single value from each 6x6 sample of raw_data and returns a single line of data '''
		# TODO: make this more efficient

		binned_data = []

		base = 0
		for i in range(0, len(raw_data[0])//6):
			binned_data.append( raw_data[0][base] )
			base += 6

		return binned_data

	def bin12(self, image_iter, bin12_method_type="SLOW"):
		''' this is an iterator that: Given an image iterator will yield binned lines '''

		img_props = next(image_iter)
		# dimensions shrink as we remove pixels
		processed_dims = img_props.processed_dims()
		processed_dims = ( processed_dims[0]//12, processed_dims[1]//12 )
		img_props.processed_dims( processed_dims )
		# each pixel is larger as binning gets larger
		pixel_scale = img_props.pixel_scale()
		pixel_scale = ( pixel_scale[0]*12, pixel_scale[1]*12 )
		img_props.pixel_scale( pixel_scale )
		yield img_props

		if bin12_method_type == "FAST":
			bin12_method = self.bin12_real_fast
		else:
			bin12_method = self.bin12_real

		raw_data = []
		line_count = 0
		for line in image_iter:
			raw_data.append( line )
			line_count += 1
			if line_count == 12:
				yield bin12_method( raw_data )
				line_count = 0
				raw_data = []

	def bin12_real(self, raw_data):
		''' does a 12x12 sample of raw_data and returns a single line of data '''

		binned_data = []

		# Filter out those unwanted hugely negative values...
		filter_fun = lambda a: self.__ignore_value.__ne__(a)

		base = 0
		for i in range(0, len(raw_data[0])//12):

			ints = list(filter( filter_fun, raw_data[0][base:base+12] +
				raw_data[1][base:base+12] +
				raw_data[2][base:base+12] +
				raw_data[3][base:base+12] +
				raw_data[4][base:base+12] +
				raw_data[5][base:base+12] +
				raw_data[6][base:base+12] +
				raw_data[7][base:base+12] +
				raw_data[8][base:base+12] +
				raw_data[9][base:base+12] +
				raw_data[10][base:base+12] +
				raw_data[11][base:base+12] ))
			len_ints = len( ints )

			# If we have all pesky values, return a pesky value
			if len_ints == 0:
				binned_data.append( self.__ignore_value )
			else:
				binned_data.append( sum(ints) / len(ints) )

			base += 12
		return binned_data

	def bin12_real_fast(self, raw_data):
		''' takes a single value from each 12x12 sample of raw_data and returns a single line of data '''
		return raw_data[0][11::12]

	def cropXY(self, image_iter, XSize=None, YSize=None, XOffset=0, YOffset=0):
		''' return a cropped portion of the image '''

		img_props = next(image_iter)
		# dimensions shrink as we remove pixels
		processed_dims = img_props.processed_dims()

		if XSize is None:
			XSize = processed_dims[0]
		if YSize is None:
			YSize = processed_dims[1]

		if XSize + XOffset > processed_dims[0]:
			XSize = processed_dims[0]
			XOffset = 0
		if YSize + YOffset > processed_dims[1]:
			YSize = processed_dims[1]
			YOffset = 0

		img_props.processed_dims( (XSize, YSize) )
		yield img_props

		currentY = 0
		for line in image_iter:
			if currentY >= YOffset and currentY <= YOffset + YSize:
				yield line[XOffset:XOffset+XSize]
			# Not much point in reading the rest of the data...
			if currentY == YOffset + YSize:
				return
			currentY += 1

	def getImage(self, img, img_props):
		''' Assumes 32-bit pixels -- bins image '''
		dims = img_props.dims()

		# setup to unpack more efficiently.
		x_len = dims[0]
		# little endian (PC_REAL)
		unpack_str = "<"
		# unpack_str = ">"
		unpack_bytes_str = "<"
		pack_bytes_str = "="
		# 32 bits/sample * samples/line = y_bytes (per line)
		x_bytes = 4*x_len
		for x in range(0, x_len):
			# 32-bit float is "d"
			unpack_str += "f"
			unpack_bytes_str += "I"
			pack_bytes_str += "I"

		# Each iterator yields this first ... it is for reference of the next iterator:
		yield img_props

		for y in range(0, dims[1]):
			# pixels is a byte array
			pixels = b''
			while len(pixels) < x_bytes:
				new_pixels = img.read( x_bytes - len(pixels) )
				pixels += new_pixels
				if len(new_pixels) == 0:
					x_bytes = -1
					pixels = []
			if len(pixels) == x_bytes:
				if 0 == 1:
					repacked_pixels = b''
					for integer in unpack(unpack_bytes_str, pixels):
						repacked_pixels += pack("=I", integer)
					yield unpack( unpack_str, repacked_pixels )
				else:
					yield unpack( unpack_str, pixels )

	def shiftToOrigin(self, image_iter, image_min_max):
		''' takes a generator and shifts the points by the valid minimum
		    also removes points with value self.__ignore_value and replaces them with None
		'''

		# use the passed in values ...
		valid_min = image_min_max[0]

		# pass on dimensions/pixel_scale since we don't modify them here
		yield next(image_iter)


		# closures rock!
		def normalize_fun(point):
			if point == self.__ignore_value:
				return None
			return point - valid_min

		for line in image_iter:
			yield list(map(normalize_fun, line))

	def scaleZ(self, image_iter, scale_factor):
		''' scales the mesh values by a factor '''
		# pass on dimensions since we don't modify them here
		yield next(image_iter)

		scale_factor = self.scale()

		def scale_fun(point):
			try:
				return point * scale_factor
			except:
				return None

		for line in image_iter:
			yield list(map(scale_fun, line))

	def genMesh(self, image_iter):
		'''Returns a mesh object from an image iterator this has the
			 value-added feature that a value of "None" is ignored
		'''

		# Get the output image size given the above transforms
		img_props = next(image_iter)

		# Let's interpolate the binned DTM with blender -- yay meshes!
		coords = []
		faces	= []
		face_count = 0
		coord = -1
		max_x = img_props.processed_dims()[0]
		max_y = img_props.processed_dims()[1]

		scale_x = self.scale() * img_props.pixel_scale()[0]
		scale_y = self.scale() * img_props.pixel_scale()[1]

		line_count = 0
		current_line = []
		# seed the last line (or previous line) with a line
		last_line = next(image_iter)
		point_offset = 0
		previous_point_offset = 0

		# Let's add any initial points that are appropriate
		x = 0
		point_offset += len( last_line ) - last_line.count(None)
		for z in last_line:
			if z != None:
				coords.append( (x*scale_x, 0.0, z) )
				coord += 1
			x += 1

		# We want to ignore points with a value of "None" but we also need to create vertices
		# with an index that we can re-create on the next line. The solution is to remember
		# two offsets: the point offset and the previous point offset.
		#     these offsets represent the point index that blender gets -- not the number of
		#     points we have read from the image

		# if "x" represents points that are "None" valued then conceptually this is how we
		# think of point indices:
		#
		# previous line: offset0   x   x  +1  +2  +3
		# current line:  offset1   x  +1  +2  +3   x

		# once we can map points we can worry about making triangular or square faces to fill
		# the space between vertices so that blender is more efficient at managing the final
		# structure.


		# read each new line and generate coordinates+faces
		for dtm_line in image_iter:

			# Keep track of where we are in the image
			line_count += 1
			y_val = line_count*-scale_y

			# Just add all points blindly
			# TODO: turn this into a map
			x = 0
			for z in dtm_line:
				if z != None:
					coords.append( (x*scale_x, y_val, z) )
					coord += 1
				x += 1

			# Calculate faces
			for x in range(0, max_x - 1):
				vals = [
					last_line[ x + 1 ],
					last_line[ x ],
					dtm_line[  x ],
					dtm_line[  x + 1 ],
					]

				# Two or more values of "None" means we can ignore this block
				none_val = vals.count(None)

				# Common case: we can create a square face
				if none_val == 0:
					faces.append( (
						previous_point_offset,
						previous_point_offset+1,
						point_offset+1,
						point_offset,
						) )
					face_count += 1
				elif none_val == 1:
					# special case: we can implement a triangular face
					## NB: blender 2.5 makes a triangular face when the last coord is 0
					# TODO: implement a triangular face
					pass

				if vals[1] != None:
					previous_point_offset += 1
				if vals[2] != None:
					point_offset += 1

			# Squeeze the last point offset increment out of the previous line
			if last_line[-1] != None:
				previous_point_offset += 1

			# Squeeze the last point out of the current line
			if dtm_line[-1] != None:
				point_offset += 1

			# remember what we just saw (and forget anything before that)
			last_line = dtm_line

		me = bpy.data.meshes.new(img_props.name()) # create a new mesh

		me.from_pydata(coords, [], faces)

		## 
		# me.vertices.add(len(coords)/3)
		# me.vertices.foreach_set("co", coords)
		# me.faces.add(len(faces)/4)
		# me.faces.foreach_set("vertices_raw", faces)

		me.update()

		bin_desc = self.bin_mode()
		if bin_desc == 'NONE':
			bin_desc = 'No Bin'

		ob=bpy.data.objects.new("DTM - %s" % bin_desc, me)

		return ob

	################################################################################
	#  Yay, done with helper functions ... let's see the abstraction in action!    #
	################################################################################
	def execute(self):

		img = open(self.__filepath, 'rb')

		(label, parsedLabel) = self.getPDSLabel(img)

		image_dims = self.getLinesAndSamples(parsedLabel)
		img_min_max_vals = self.getValidMinMax(parsedLabel)
		self.__ignore_value = self.getMissingConstant(parsedLabel)

		# MAGIC VALUE? -- need to formalize this to rid ourselves of bad points
		img.seek(28)
		# Crop off 4 lines
		img.seek(4*image_dims[0])

		# HiRISE images (and most others?) have 1m x 1m pixels
		pixel_scale=(1, 1)

		# The image we are importing
		image_name = os.path.basename( self.__filepath )

		# Set the properties of the image in a manageable object
		img_props = image_properties( image_name, image_dims, pixel_scale )

		# Get an iterator to iterate over lines
		image_iter = self.getImage(img, img_props)

		## Wrap the image_iter generator with other generators to modify the dtm on a
		## line-by-line basis. This creates a stream of modifications instead of reading
		## all of the data at once, processing all of the data (potentially several times)
		## and then handing it off to blender
		## TODO: find a way to alter projection based on transformations below

		if self.__cropXY:
			image_iter = self.cropXY(image_iter,
				XSize=self.__cropXY[0], 
				YSize=self.__cropXY[1],
				XOffset=self.__cropXY[2],
				YOffset=self.__cropXY[3]
				)

		# Select an appropriate binning mode
		## TODO: generalize the binning fn's
		bin_mode = self.bin_mode()
		bin_mode_funcs = {
			'BIN2': self.bin2(image_iter),
			'BIN6': self.bin6(image_iter),
			'BIN6-FAST': self.bin6(image_iter, 'FAST'),
			'BIN12': self.bin12(image_iter),
			'BIN12-FAST': self.bin12(image_iter, 'FAST')
			}
		if bin_mode in bin_mode_funcs.keys():
			image_iter = bin_mode_funcs[ bin_mode ]

		image_iter = self.shiftToOrigin(image_iter, img_min_max_vals)

		if self.scale != 1.0:
			image_iter = self.scaleZ(image_iter, img_min_max_vals)

		# Create a new mesh object and set data from the image iterator
		ob_new = self.genMesh(image_iter)

		if img:
			img.close()

		# Add mesh object to the current scene
		for s in bpy.data.scenes:
			scene = s
		scene.objects.link(ob_new)
		scene.update()

		# deselect other objects
		bpy.ops.object.select_all(action='DESELECT')

		# scene.objects.active = ob_new
		# Select the new mesh
		ob_new.select = True

		return ob_new

################################################################################
## How do we setup our default render context?
################################################################################
class DTMViewerRenderContext:
	# This clears the scene and creates:
	#   1 DTM Mesh (using the hirise_dtm_importer class above)
	#   1 Lamp (Sun)
	#   1 Camera
	#   1 Empty (CameraTarget)

	def __init__(self,dtm_img,dtm_texture=None,framesPerOrbit=72):
		self.__img = dtm_img
		self.__texture = dtm_texture
		self.__framesPerOrbit = framesPerOrbit
		self.__orbitsPerDTM = 1

	def createDefaultContext(self):
		''' clears the current scene and fills it with a DTM '''
		self.clearScene()
		self.addEmptyTarget()
		self.addCirclePath()
		self.setupCamera()
		self.setupRender()
		self.setupLightSource()
		self.addDTM()
		self.cleanupView()
		self.adjustCameraTarget()

	# Adds the Empty target for the camera to track
	def addEmptyTarget(self):
		# Add an empty object called CameraTarget
		bpy.ops.object.add(type = 'EMPTY')
		for o in filter( lambda o:o.type=='EMPTY', bpy.data.objects ):
		  mt = o
		mt.name = 'CameraTarget'
		self.__CameraTarget = mt

	# Adds the path for the camera to follow
	def addCirclePath(self):
		# Add a circular path
		bpy.ops.curve.primitive_bezier_circle_add()
		bpy.ops.object.parent_set(type='FOLLOW')

		for o in filter( lambda o:o.type=='CURVE', bpy.data.objects ):
		  crv = o
		for o in bpy.data.curves:
		  o.path_duration = self.__framesPerOrbit * self.__orbitsPerDTM
		crv.name = 'CirclePath'
		for o in crv.children:
		  o.path_duration = self.__framesPerOrbit * self.__orbitsPerDTM
		self.__CameraPath = crv

	# Clear the scene by removing all objects/materials
	def clearScene(self):
		bpy.ops.object.select_all(action='SELECT')
		bpy.ops.object.delete()
		for mat in bpy.data.materials:
			bpy.data.materials.remove(mat)

	# Setup a camera to track our empty target
	def setupCamera(self,Z=0.0):
		# Create a new default camera
		bpy.ops.object.camera_add()
		for camera in filter( lambda o:o.type=='CAMERA', bpy.data.objects ):
			pass

		# Set the camera above the origin
		camera.location[2] = 0.0 + Z
		camera.name = "Camera"
		# The camera needs to be able to see "far away"
		camera.data.clip_end = 500.0
		# Set the scene to use the camera and to use the correct number of frames
		for scene in bpy.data.scenes:
			scene.camera = camera
			scene.frame_end = self.__framesPerOrbit * self.__orbitsPerDTM

		# Find the camera target object
		for camera_target in filter(
			lambda o:o.name=="CameraTarget",
			bpy.data.objects
			):
				pass

		bpy.ops.object.select_pattern(pattern=camera.name)
		bpy.ops.object.constraint_add(type='FOLLOW_PATH')
		bpy.ops.object.constraint_add(type='TRACK_TO')
		for constraint in camera.constraints:
			# always watch the camera target
			if constraint.type == 'TRACK_TO':
				constraint.target = camera_target
				constraint.track_axis = 'TRACK_NEGATIVE_Z'
				constraint.up_axis = 'UP_Y'
			# always stay 100 units away from the target
			if constraint.type == 'FOLLOW_PATH':
				constraint.target = self.__CameraPath
				constraint.forward_axis = 'TRACK_NEGATIVE_Z'
				constraint.up_axis = 'UP_Y'
				self.__cameraPathConstraint = constraint

	def setupLightSource(self):
		# The default "SUN" points straight down, which is fine for our needs
		bpy.ops.object.lamp_add(type='SUN')

	# Set the rendering defaults
	def setupRender(self):
		render = bpy.context.scene.render
		# Don't bother raytracing since we will likely put a real image on the
		# mesh that already contains shadows
		render.use_raytrace = False
		render.resolution_x = 1920
		render.resolution_y = 1080
		render.resolution_percentage = 100

	# Add the DTM to the scene
	def addDTM(self):
		helper = hirise_dtm_importer(self.__img)
		helper.bin_mode( 'BIN6' )
		helper.scale( 0.01 )
		dtm_mesh = helper.execute()

		bpy.ops.object.select_pattern(pattern=dtm_mesh.name)

		# Initialize a new material
		mat = bpy.data.materials.new(name="DTMSurface")
		mat.specular_intensity = 0.0
		mat.diffuse_intensity = 0.0
		mat.use_shadeless = True

		# Create a texture (to be modified by the user)
		if not self.__texture is None:
			tex = bpy.data.textures.new(name="DTMTexture",type='IMAGE')
			try:
				bpy.ops.file.make_paths_absolute()
				bpy.ops.file.pack_all()
				tex.image = bpy.data.images.load( self.__texture )
				## ... maybe we need relative_path=False and bpy.ops.image.open ?
				# print("tex.image: ", tex.image)
				# print("tex.image.filepath: ", tex.image.filepath)
				# print("tex.image.filepath_raw: ", tex.image.filepath_raw)
				bpy.ops.image.pack()
				# print("tex.image.packed_file: ", tex.image.packed_file)
				# bpy.ops.image.pack()
			except:
				raise NameError("Could not load image",self.__texture)
		else:
			# Just use a default BLEND texture
			# The user can override this later
			tex = bpy.data.textures.new(name="DTMTexture",type='BLEND')

		mtex = mat.texture_slots.add()
		mtex.texture = tex
		mtex.color = (0.0,0.0,0.0)

		# Add a material to the DTM object
		dtm_mesh.data.materials.append(mat)

		# Center CameraTarget on DTM
		x = tuple(map( lambda xyz: xyz[0], dtm_mesh.bound_box ))
		y = tuple(map( lambda xyz: xyz[1], dtm_mesh.bound_box ))
		z = tuple(map( lambda xyz: xyz[2], dtm_mesh.bound_box ))
		self.__dtm_min_v = (min(x),min(y),min(z))
		self.__dtm_max_v = (max(x),max(y),max(z))

	#
	# Add some custom stereo properties to the selected camera
	# Taken from Sebastian Schneider's wonderful stereoscopic camera plugin
	#   http://www.noeol.de/s3d (released on Jun/05/2011)
	# This should allow the plugin to work properly with the stereo camera we create here
	#
	bpy.types.Object.stereo_camera_separation = bpy.props.FloatProperty(
		attr="stereo_camera_separation",
		name='stereo_camera_separation',
		description='Camera Separation in 1/1000 Blender Units',
		min=0.0, soft_min=0.0, max=10000, soft_max=10000, default=600)

	bpy.types.Object.stereo_focal_distance = bpy.props.FloatProperty(
		attr="stereo_focal_distance",
		name='stereo_focal_distance', 
		description='Distance to the Stereo-Window (Zero Parallax) in Blender Units',
		min=0.0, soft_min=0.0, max=1000, soft_max=1000, default=75)

	bpy.types.Object.max_parallax = bpy.props.FloatProperty(
		attr="max_parallax",
		name="max_parallax", 
		description='Max parallax angle in degree. Default 1.0', 
		min=0.0, soft_min=0.0, max=3.0, soft_max=3.0, default=1.0)

	bpy.types.Object.near_plane_distance = bpy.props.FloatProperty(
		attr="near_plane_distance",
		name="near_plane_distance", 
		description='Distance to Near-Plane in Blender Units (has no effect on the stereo output)',
		min=0.0, soft_min=0.0, max=100000, soft_max=100000, default=10)

	bpy.types.Object.far_plane_distance = bpy.props.FloatProperty(
		attr="far_plane_distance", 
		name="far_plane_distance",
		description='Distance to Far-Plane in Blender Units (has no effect on the stereo output)',
		min=0.0, soft_min=0.0, max=100000, soft_max=100000, default=500)

	bpy.types.Object.viewer_distance = bpy.props.FloatProperty(
		attr="viewer_distance",
		name="viewer_distance", 
		description='Distance between Viewer and the Projection Screen (e.g. Theater canvas, Stereo-TV or Display) in inch', 
		min=0.0, soft_min=0.0, max=10000, soft_max=10000, default=20)

	bpy.types.Object.stereo_camera_shift_x = bpy.props.FloatProperty(
		attr="stereo_camera_shift_x",
		name="stereo_camera_shift_x")

	bpy.types.Object.stereo_camera_delta = bpy.props.FloatProperty(
		attr="stereo_camera_delta", 
		name="stereo_camera_delta")

	bpy.types.Object.max_disparity = bpy.props.FloatProperty(
		attr="max_disparity", 
		name="max_disparity")

	bpy.types.Object.toein_angle = bpy.props.FloatProperty(
		attr="toein_angle", 
		name="toein_angle")

	bpy.types.Object.screen_ppi = bpy.props.IntProperty(
		attr="screen_ppi",
		name="screen_ppi", 
		description='Pixel per Inch on the Projection Screen (Theater Canvas, Stereo TV or Display)', 
		min=1, soft_min=1, max=1000, soft_max=1000, default=96)

	bpy.types.Object.show_stereo_window = bpy.props.BoolProperty(
		attr="show_stereo_window", 
		name="show_stereo_window", 
		default=True)

	bpy.types.Object.show_near_far_plane = bpy.props.BoolProperty(
		attr="show_near_far_plane", 
		name="show_near_far_plane", 
		default=False)	

	bpy.types.Object.camera_type = bpy.props.EnumProperty(
		attr="camera_type",
		items=( ("OFFAXIS", "Off-Axis", "Default (best stereo result)"),
			("CONVERGE", "Converge", "Toe-In Camera (could create uncomfortable vertical parallax)"),
			("PARALLEL", "Parallel", "Simple stereo camera (zero parallax at infinity)")),
		name="camera_type", 
		description="", 
		default="OFFAXIS")

	def setup3dCamera(self):
		# Heavily influenced by Sebastian Schneider's plugin with
		# even heavier modifications for simplicity and supporting
		# only an OFFAXIS camera here. Since it is compatible with
		# the original plugin the camera type can be changed
		# manually inside of blender.
		camera = bpy.context.scene.camera

		# Add left camera
		bpy.ops.object.select_all(action='DESELECT')
		bpy.context.scene.objects.active = camera
		left_cam = bpy.data.cameras.new('L_' + camera.name)
		lc_obj = bpy.data.objects.new('L_' + camera.name, left_cam)
		bpy.context.scene.objects.link(lc_obj)

		# Add right camera
		bpy.ops.object.select_all(action='DESELECT')
		bpy.context.scene.objects.active = camera
		right_cam = bpy.data.cameras.new('R_' + camera.name)
		rc_obj = bpy.data.objects.new('R_' + camera.name, right_cam)
		bpy.context.scene.objects.link(rc_obj)

		# Keep the focal point (zero parallax) at the center of the
		# mesh
		camera.stereo_focal_distance = self.__camera_xy_distance

		# Make a reasonable separation for the stereo camera effect
		camera.stereo_camera_separation = self.__camera_xy_distance * 7

		# Get/configure stereo camera parameters
		stereo_base = camera.stereo_camera_separation/1000 # 1/1000 Blender Units
		focal_dist = camera.stereo_focal_distance
		camera_fov = camera.data.angle
		theta = camera.max_parallax
		viewer_dist = camera.viewer_distance
		ppi = camera.screen_ppi
		# get the horizonal render resolution
		render_width = bpy.context.scene.render.resolution_x
		# calculate delta and shift
		camera.stereo_camera_delta = (render_width*stereo_base)/(2*focal_dist*math.tan(camera_fov/2))
		camera.stereo_camera_shift_x = camera.stereo_camera_delta/render_width

                # set the left camera
		left_cam.angle = camera.data.angle
		left_cam.clip_start = camera.data.clip_start
		left_cam.clip_end = camera.data.clip_end
		left_cam.dof_distance = camera.data.dof_distance
		left_cam.dof_object = camera.data.dof_object
		left_cam.shift_y = camera.data.shift_y
		left_cam.shift_x = (camera.stereo_camera_shift_x/2)+camera.data.shift_x
		lc_obj.location = -(camera.stereo_camera_separation/1000)/2,0,0
		lc_obj.rotation_euler = (0.0,0.0,0.0) # reset 

		# set the right camera
		right_cam.angle = camera.data.angle
		right_cam.clip_start = camera.data.clip_start
		right_cam.clip_end = camera.data.clip_end
		right_cam.dof_distance = camera.data.dof_distance
		right_cam.dof_object = camera.data.dof_object
		right_cam.shift_y = camera.data.shift_y
		right_cam.shift_x = -(camera.stereo_camera_shift_x/2)+camera.data.shift_x
		rc_obj.location = (camera.stereo_camera_separation/1000)/2,0,0
		rc_obj.rotation_euler = (0.0,0.0,0.0) # reset

		# add the left/right camera as child 
		lc_obj.parent = camera
		rc_obj.parent = camera

		# Add Left render scene
		bpy.ops.scene.new(type='LINK_OBJECTS')
		bpy.context.scene.name = "Scene.Left"
		bpy.context.scene.camera = lc_obj
		bpy.ops.object.select_all(action='DESELECT')
		bpy.context.screen.scene = bpy.data.scenes['Scene']

		# Add Right render scene
		bpy.ops.scene.new(type='LINK_OBJECTS')
		bpy.context.scene.name = "Scene.Right"
		bpy.context.scene.camera = rc_obj
		bpy.ops.object.select_all(action='DESELECT')

		# Add composit render scene
		bpy.ops.scene.new(type='LINK_OBJECTS')
		bpy.context.scene.name = "Scene.Composite"
		bpy.context.scene.camera = camera
		bpy.ops.object.select_all(action='DESELECT')

	def setupOverlayCompositing(self, fgImgPath, bgImgPath):
		# Store imported images in the .blend
		bpy.ops.file.make_paths_absolute()
		bpy.ops.file.pack_all()

		# Use compositing for our render...
		Scene = bpy.data.scenes['Scene.Composite']
		Scene.use_nodes = True

		# cleanup
		Tree = Scene.node_tree
		Tree.links.remove( Tree.links[0] )

		def fg_bg_composite(Tree, Src_output, Dst_input, fgImgPath, bgImgPath):
			''' Adds two groups for the fg/bg images '''

			FG_Node = bpy.data.node_groups.new("ForegroundImage", type='COMPOSITE')
			BG_Node = bpy.data.node_groups.new("BackgroundImage", type='COMPOSITE')

			FG_Node.inputs.new("Source", 'RGBA')
			FG_Node.outputs.new('Result', 'RGBA')

			FG_Image = FG_Node.nodes.new('IMAGE')
			FG_Image.image = bpy.data.images.load( fgImgPath )
			FG_Alpha = FG_Node.nodes.new('ALPHAOVER')

			FG_Node.links.new(FG_Image.outputs['Image'], FG_Alpha.inputs[2])
			FG_Node.links.new(FG_Node.inputs["Source"], FG_Alpha.inputs[1])
			FG_Node.links.new(FG_Node.outputs['Result'], FG_Alpha.outputs['Image'])

			# Add foreground image compositing
			newFGGroup = Tree.nodes.new("GROUP", group = FG_Node)
			Tree.links.new(newFGGroup.inputs[0], Src_output)

			BG_Node.inputs.new("Source", 'RGBA')
			BG_Node.outputs.new('Result', 'RGBA')

			BG_Image = BG_Node.nodes.new('IMAGE')
			BG_Image.image = bpy.data.images.load( bgImgPath )

			BG_Alpha = BG_Node.nodes.new('ALPHAOVER')

			BG_Node.links.new(BG_Image.outputs['Image'], BG_Alpha.inputs[1])
			BG_Node.links.new(BG_Node.inputs["Source"], BG_Alpha.inputs[2])
			BG_Node.links.new(BG_Node.outputs['Result'], BG_Alpha.outputs['Image'])

			# Add background image compositing
			newBGGroup = Tree.nodes.new("GROUP", group = BG_Node)
			Tree.links.new(newBGGroup.inputs[0], newFGGroup.outputs[0])
			if Dst_input:
				Tree.links.new(newBGGroup.outputs[0], Dst_input)

			# return the image output of the fg/bg node
			return newBGGroup.outputs[0]

		def top_bottom_composite(Scene, Tree, L_Src_output, R_Src_output, Dst_input):
			''' Adds a top/bottom stereo render pipeline '''
			res_x = Scene.render.resolution_x
			res_y = Scene.render.resolution_y

			# Create a canvas image (if needed) of the appropriate size
			img_name = 'canvas'+str(res_x)+'x'+str(res_y*2)
			try:
				img = bpy.data.images[img_name]
			except:
				bpy.ops.image.new(
					name=img_name,
					width=res_x,
					height=(res_y*2),
					color=(0,0,0,1)
					)
				img = bpy.data.images[img_name]

			# Create a node group to help encapsulate this logic
			TB_Node = bpy.data.node_groups.new("TopBottom", type='COMPOSITE')
			TB_Node.inputs.new('L_Image', 'RGBA')
			TB_Node.inputs.new('R_Image', 'RGBA')
			TB_Node.outputs.new('Image', 'RGBA')

			# Add top/bottom compositing group to screen
			newTBGroup = Tree.nodes.new("GROUP", group = TB_Node)
			Tree.links.new(newTBGroup.inputs['L_Image'], L_Src_output)
			Tree.links.new(newTBGroup.inputs['R_Image'], R_Src_output)
			if Dst_input:
				Tree.links.new(newTBGroup.outputs['Image'], Dst_input)

			# Create a compositing node with the canvas image
			canvas = TB_Node.nodes.new('IMAGE')
			canvas.image = img
			canvas.location = (-120,7)

			# Add translation nodes
			top_translate = TB_Node.nodes.new('TRANSLATE')
			top_translate.location = (-120, -260)
			top_translate.inputs['X'].default_value = encap_1(0.0)
			top_translate.inputs['Y'].default_value = encap_1(int(res_y/2))

			bottom_translate = TB_Node.nodes.new('TRANSLATE')
			top_translate.location = (-120, -383)
			bottom_translate.inputs['X'].default_value = encap_1(0.0)
			bottom_translate.inputs['Y'].default_value = encap_1(-int(res_y/2))

			# Add screen nodes
			screen_top = newTBGroup.node_tree.nodes.new('MIX_RGB')
			screen_top.location = (70,7)
			screen_top.blend_type = 'SCREEN'
			screen_top.inputs[0].default_value = encap_1(1.0)

			screen_bottom = newTBGroup.node_tree.nodes.new('MIX_RGB')
			screen_bottom.location = (250,7)
			screen_bottom.blend_type = 'SCREEN'
			screen_bottom.inputs[0].default_value = encap_1(1.0)

			# Left input to top of screen
			newTBGroup.node_tree.links.new(TB_Node.inputs['L_Image'], top_translate.inputs['Image'])
			newTBGroup.node_tree.links.new(canvas.outputs['Image'], screen_top.inputs[1])
			newTBGroup.node_tree.links.new(top_translate.outputs['Image'], screen_top.inputs[2])

			# Right input to bottom of screen
			newTBGroup.node_tree.links.new(TB_Node.inputs['R_Image'], bottom_translate.inputs['Image'])
			newTBGroup.node_tree.links.new(screen_top.outputs['Image'], screen_bottom.inputs[1])
			newTBGroup.node_tree.links.new(bottom_translate.outputs['Image'], screen_bottom.inputs[2])

			# Scale result to match render output
			scale = newTBGroup.node_tree.nodes.new('SCALE')
			scale.space = 'RELATIVE'
			scale.inputs['Y'].default_value = encap_1(0.5)
			scale.location = (400, 7)
			newTBGroup.node_tree.links.new(screen_bottom.outputs['Image'], scale.inputs['Image'])
			newTBGroup.node_tree.links.new(TB_Node.outputs['Image'], scale.outputs['Image'])

			# return the new group
			return newTBGroup

		def left_right_composite(Scene, Tree, L_Src_output, R_Src_output, Dst_input):
			''' Adds a left/right stereo render pipeline '''
			res_x = Scene.render.resolution_x
			res_y = Scene.render.resolution_y

			# Create a canvas image (if needed) of the appropriate size
			img_name = 'canvas'+str(res_x*2)+'x'+str(res_y)
			try:
				img = bpy.data.images[img_name]
			except:
				bpy.ops.image.new(
					name=img_name,
					width=(res_x*2),
					height=res_y,
					color=(0,0,0,1)
					)
				img = bpy.data.images[img_name]

			# Create a node group to help encapsulate this logic
			LR_Node = bpy.data.node_groups.new("LeftRight", type='COMPOSITE')
			LR_Node.inputs.new('L_Image', 'RGBA')
			LR_Node.inputs.new('R_Image', 'RGBA')
			LR_Node.outputs.new('Image', 'RGBA')

			# Add left/right compositing group to screen
			newLRGroup = Tree.nodes.new("GROUP", group = LR_Node)
			Tree.links.new(newLRGroup.inputs['L_Image'], L_Src_output)
			Tree.links.new(newLRGroup.inputs['R_Image'], R_Src_output)
			if Dst_input:
				Tree.links.new(newLRGroup.outputs['Image'], Dst_input)

			# Create a compositing node with the canvas image
			canvas = LR_Node.nodes.new('IMAGE')
			canvas.image = img
			canvas.location = (-120,7)

			# Add translation nodes
			left_translate = LR_Node.nodes.new('TRANSLATE')
			left_translate.location = (-120, -260)
			left_translate.inputs['X'].default_value = encap_1(int(res_x/2))
			left_translate.inputs['Y'].default_value = encap_1(0)

			right_translate = LR_Node.nodes.new('TRANSLATE')
			left_translate.location = (-120, -383)
			right_translate.inputs['X'].default_value = encap_1(-int(res_x/2))
			right_translate.inputs['Y'].default_value = encap_1(0)

			# Add screen nodes
			screen_left = newLRGroup.node_tree.nodes.new('MIX_RGB')
			screen_left.location = (70,7)
			screen_left.blend_type = 'SCREEN'
			screen_left.inputs[0].default_value = encap_1(1.0)

			screen_right = newLRGroup.node_tree.nodes.new('MIX_RGB')
			screen_right.location = (250,7)
			screen_right.blend_type = 'SCREEN'
			screen_right.inputs[0].default_value = encap_1(1.0)

			# Left input to left of screen
			newLRGroup.node_tree.links.new(LR_Node.inputs['L_Image'], left_translate.inputs['Image'])
			newLRGroup.node_tree.links.new(canvas.outputs['Image'], screen_left.inputs[1])
			newLRGroup.node_tree.links.new(left_translate.outputs['Image'], screen_left.inputs[2])

			# Right input to right of screen
			newLRGroup.node_tree.links.new(LR_Node.inputs['R_Image'], right_translate.inputs['Image'])
			newLRGroup.node_tree.links.new(screen_left.outputs['Image'], screen_right.inputs[1])
			newLRGroup.node_tree.links.new(right_translate.outputs['Image'], screen_right.inputs[2])

			# Scale result to match render output
			scale = newLRGroup.node_tree.nodes.new('SCALE')
			scale.space = 'RELATIVE'
			scale.inputs['X'].default_value = encap_1(0.5)
			scale.location = (400, 7)
			newLRGroup.node_tree.links.new(screen_right.outputs['Image'], scale.inputs['Image'])
			newLRGroup.node_tree.links.new(LR_Node.outputs['Image'], scale.outputs['Image'])

			# return the new group
			return newLRGroup


		def rc_composite(Scene, Tree, L_Src_output, R_Src_output, Dst_input):
			''' Adds one group for the red/cyan stereo image '''

			RC_Node = bpy.data.node_groups.new("RedCyanImage", type='COMPOSITE')
			RC_Node.inputs.new('L_Image', 'RGBA')
			RC_Node.inputs.new('R_Image', 'RGBA')
			RC_Node.outputs.new('Image', 'RGBA')

			SepRGB_Left = RC_Node.nodes.new('SEPRGBA')
			SepRGB_Right = RC_Node.nodes.new('SEPRGBA')
			CombRGB = RC_Node.nodes.new('COMBRGBA')

			# Red from left channel, BlueGreen from right
			RC_Node.links.new(SepRGB_Left.outputs['R'], CombRGB.inputs['R'])
			RC_Node.links.new(SepRGB_Right.outputs['B'], CombRGB.inputs['B'])
			RC_Node.links.new(SepRGB_Right.outputs['G'], CombRGB.inputs['G'])

			RC_Node.links.new(RC_Node.inputs["L_Image"], SepRGB_Left.inputs['Image'])
			RC_Node.links.new(RC_Node.inputs["R_Image"], SepRGB_Right.inputs['Image'])
			RC_Node.links.new(RC_Node.outputs['Image'], CombRGB.outputs['Image'])

			# Add foreground image compositing
			newRCGroup = Tree.nodes.new("GROUP", group = RC_Node)
			Tree.links.new(newRCGroup.inputs['L_Image'], L_Src_output)
			Tree.links.new(newRCGroup.inputs['R_Image'], R_Src_output)
			if Dst_input:
				Tree.links.new(newRCGroup.outputs['Image'], Dst_input)

			# return the new group
			return newRCGroup

		# Reconfigure default source/destination
		R_Src = Tree.nodes["Render Layers"]
		R_Src.name = "Render Layers.Right"
		R_Src.scene = bpy.data.scenes['Scene.Right']
		R_Src_output = R_Src.outputs['Image']
		Default_Dst = Tree.nodes["Composite"]

		# Right camera output to the default destination input
		# R_Src_output becomes the output of the fg/bg composite stream
		R_Src_output = fg_bg_composite(
			Tree,
			R_Src_output,
			Default_Dst.inputs['Image'],
			fgImgPath,
			bgImgPath)

		# Add a similar source for the left channel
		L_Src = Tree.nodes.new('R_LAYERS')
		L_Src.name = "Render Layers.Left"
		L_Src.scene = bpy.data.scenes['Scene.Left']
		L_Src_output = L_Src.outputs['Image']

		# Add a similar fg/bg composite path for the left channel
		L_Src_output = fg_bg_composite(
			Tree,
			L_Src_output,
			None,
			fgImgPath,
			bgImgPath)

		# Add a top/bottom composite file output
		tb_file_output_node = Tree.nodes.new('OUTPUT_FILE')
		tb_file_output_node.name = "File Output.TB"
		tb_file_output_node.base_path = '//tb'
		try:
			tb_file_output_node.image_type = 'PNG'
		except Exception:
			try:
				tb_file_output_node.image_settings.file_format = 'PNG'
			except Exception:
				tb_file_output_node.format.file_format = 'PNG'

		tbGroup = top_bottom_composite(
			Scene,
			Tree,
			L_Src_output,
			R_Src_output,
			tb_file_output_node.inputs['Image'])

		# Add a red/cyan composite file output
		rc_file_output_node = Tree.nodes.new('OUTPUT_FILE')
		rc_file_output_node.name = "File Output.RC"
		rc_file_output_node.base_path = '//rc'
		try:
			rc_file_output_node.image_type = 'PNG'
		except Exception:
			try:
				rc_file_output_node.image_settings.file_format = 'PNG'
			except Exception:
				rc_file_output_node.format.file_format = 'PNG'

		rcGroup = rc_composite(
			Scene, 
			Tree,
			L_Src_output,
			R_Src_output,
			rc_file_output_node.inputs['Image'])

		# Add a left/right composite file output
		lr_file_output_node = Tree.nodes.new('OUTPUT_FILE')
		lr_file_output_node.name = "File Output.LR"
		lr_file_output_node.base_path = '//lr'
		try:
			lr_file_output_node.image_type = 'PNG'
		except Exception:
			try:
				lr_file_output_node.image_settings.file_format = 'PNG'
			except Exception:
				lr_file_output_node.format.file_format = 'PNG'

		lrGroup = left_right_composite(
			Scene,
			Tree,
			L_Src_output,
			R_Src_output,
			lr_file_output_node.inputs['Image'])

		# Why I need this again, I don't know. Must be a bug.
		# Tree.links.new(R_Src_output, Default_Dst.inputs['Image'])
		# bg_l=Tree.nodes['BackgroundImage'].outputs['Result']
		# bg_r=Tree.nodes['BackgroundImage.001'].outputs['Result']

		# Tree.links.new(bg_l, rcGroup.inputs['L_Image'])
		# Tree.links.new(bg_r, rcGroup.inputs['R_Image'])

		# Tree.links.new(bg_l, tbGroup.inputs['L_Image'])
		# Tree.links.new(bg_r, tbGroup.inputs['R_Image'])

		bpy.context.screen.scene = Scene

	def adjustCameraTarget(self):
		''' Attempts to move Camera/CameraTarget into "nice" places '''
		min_v = self.__dtm_min_v
		max_v = self.__dtm_max_v

		avg_v = tuple(map( lambda a,b: (a+b)/2, min_v, max_v ))
		delta_v = tuple(map( lambda a,b: abs(a-b), min_v, max_v ))
		self.__CameraTarget.location = avg_v

		xy_distance = math.sqrt( delta_v[0]**2 + delta_v[1]**2 )
		y_elev = math.sqrt( xy_distance**2 + delta_v[2]**2 )
		self.__CameraPath.location = (avg_v[0], avg_v[1], (min_v[2] + y_elev)/2)
		self.__CameraPath.scale = ( xy_distance, xy_distance, 1.0 )
		# Save for later...
		self.__camera_xy_distance = xy_distance

	def cleanupView(self):
		## Can't align view because there is no pane to apply the view
		# bpy.ops.view3d.view_all(center=True)
		bpy.ops.object.select_pattern(pattern="CameraTarget")

	def saveAs( self, path ):
		bpy.ops.wm.save_as_mainfile( filepath=path, check_existing=False )

# Quick environment helper fn
def envDefaltVal(envVar,defaultVal):
	try:
		return os.environ[envVar]
	except:
		return defaultVal

################################################################################
## Now, do all of the work
################################################################################

dtm_location=os.environ['DTM_IMG']
texture_location=envDefaltVal('DTM_TEXTURE',None)
framesPerOrbit=int(envDefaltVal('FRAMES_PER_ORBIT',72))

newScene = DTMViewerRenderContext(
	dtm_img=dtm_location,
	dtm_texture=texture_location,
	framesPerOrbit=framesPerOrbit
	)
newScene.createDefaultContext()
newScene.setup3dCamera()
newScene.setupOverlayCompositing(
	fgImgPath="/HiRISE/Users/tims/DTM_blender/foreground.tiff",
	bgImgPath="/HiRISE/Users/tims/DTM_blender/background.tiff"
	)

try:
	blend_location=os.environ['DTM_BLEND']
	newScene.saveAs( blend_location )
	print("Saved", blend_location)
	print("  DTM_IMG:", dtm_location)
	print("  DTM_TEXTURE:", texture_location)
	print("  frames per orbit::", framesPerOrbit)
except:
	print("Not saving blend file...")

# print all objects (for debugging)
# for obj in bpy.data.objects:
#print("Scene objects:")
#for obj in bpy.data.objects:
#	print('	', obj.name, '(', obj.type ,'):', obj.location, ' :: ', obj.select)
