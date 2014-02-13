#!BPY

# """
# Name: 'HiRISE PDS IMG DTM'
# Blender: 250
# Group: 'Import'
# Tooltip: 'Imports a HiRISE DTM that is formatted as a PDS IMG file'
# """

# __author__ = "Tim Spriggs"
# __email__ = "tims@arizona.edu"

bl_addon_info = {
	"name": "Import a HiRISE DTM",
	"author": "Tim Spriggs (tims@uahirise.org)",
	"version": (0,1),
	"blender": (2,5,3),
	"api": 31998,
	"location": "File > Import > HiRISE DTM (.IMG)",
	"description": "Import a HiRISE DTM formatted as a PDS IMG file",
	"warning": "This is experimental quality code",
	"category": "Import/Export"}

"""
This script can import a HiRISE DTM .IMG file.
"""

import bpy
from bpy.props import *
from io_utils import ImportHelper
from struct import pack, unpack, unpack_from
import os

class ImportHiRISEIMGDTM(bpy.types.Operator, ImportHelper):
    '''Import a HiRISE DTM formatted as a PDS IMG file'''
    bl_idname = "import_shape.img"
    bl_label  = "Import HiRISE DTM from PDS IMG"

    filename_ext = ".IMG"
    filter_glob = StringProperty(default="*.IMG", options={'HIDDEN'})

    def init_dbg(self):
      self.__dbg = open('/tmp/dbg.status', 'ab', 0)

    def dbg(self, mesg):
      if self.__dbg:
        self.__dbg.write(mesg)
        # self.__dbg.flush()

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
      if not currentObjectName == None:
        endStr = "END_OBJECT = %s" % currentObjectName
      line = ""

      while not line.rstrip() == endStr:
        line = next(labelIter)

        # print "'%s', %s, %s" % ( level, currentObjectName, line ),

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
             self.parsePDSLabel(labelIter, objName.lstrip().rstrip(), level + "  ")
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

      # print "image dimensions: %d,%d" % (line_samples, lines)
      return ( line_samples, lines )

    ############################################################################
    ## Image operations
    ############################################################################

    def bin2(self, image_iter, bin2_method_type="SLOW"):
      ''' this is an iterator that: Given an image iterator will yield binned lines '''

      (orig_dims, processed_dims) =  next(image_iter)
      processed_dims = ( processed_dims[0]//2, processed_dims[1]//2 )
      yield (orig_dims, processed_dims)

      # Take two lists  [a1, a2, a3], [b1, b2, b3] and combine them into one
      # list of [a1 + b1, a2+b2,  ... ] as long as both values are not ignorable
      combine_fun = lambda a, b: a != self.__ignore_value and b != self.__ignore_value and a + b or self.__ignore_value

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
        last_line = line
        line_count += 1

    def bin6(self, image_iter, bin6_method_type="SLOW"):
      ''' this is an iterator that: Given an image iterator will yield binned lines '''

      (orig_dims, processed_dims) =  next(image_iter)
      processed_dims = ( int(processed_dims[0]/6), int(processed_dims[1]/6) )
      yield (orig_dims, processed_dims)

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

      # Filter out those unwanted hugely negative values...
      filter_fun = lambda a: self.__ignore_value.__ne__(a)

      base = 0
      for i in range(0, len(raw_data[0])//6):

        ints = list(filter( filter_fun, raw_data[0][base:base+6] +
          raw_data[1][base:base+6] +
          raw_data[2][base:base+6] +
          raw_data[3][base:base+6] +
          raw_data[4][base:base+6] +
          raw_data[5][base:base+6] ))
        len_ints = len( ints )

        # If we have all pesky values, return a pesky value
        if len_ints == 0:
          binned_data.append( self.__ignore_value )
        else:
          binned_data.append( sum(ints) / len(ints) )

        base += 6
      return binned_data

    def bin6_real_fast(self, raw_data):
      ''' takes a single value from each 6x6 sample of raw_data and returns a single line of data '''
      # TODO: make this more efficient

      binned_data = []

      # Filter out those unwanted hugely negative values...
      filter_fun = lambda a: a < -3e-38

      base = 0
      for i in range(0, len(raw_data[0])//6):
        binned_data.append( raw_data[0][base] )
        base += 6

      return binned_data

    def cropXY(self, image_iter, XSize=None, YSize=None, XOffset=0, YOffset=0):
      ''' return a cropped portion of the image '''

      (orig_dims, upstream_dims) =  next(image_iter)
      if XSize == None:
        XSize = upstream_dims[0]
      if YSize == None:
        YSize = upstream_dims[1]

      if XSize + XOffset > upstream_dims[0]:
        self.dbg("WARNING: Upstream dims are larger than cropped XSize dim")
        XSize = upstream_dims[0]
        XOffset = 0
      if YSize + YOffset > upstream_dims[1]:
        self.dbg("WARNING: Upstream dims are larger than cropped YSize dim")
        YSize = upstream_dims[1]
        YOffset = 0

      cropped_dims = ( XSize, YSize )
      yield (orig_dims, cropped_dims)

      currentY = 0
      for line in image_iter:
        if currentY >= YOffset and currentY <= YOffset + YSize:
          yield line[XOffset:XOffset+XSize]
        # Not much point in reading the rest of the data...
        if currentY == YOffset + YSize:
          return
        currentY += 1

    def getImage(self, img, dims):
      ''' Assumes 32-bit pixels -- bins image '''
      self.dbg("getting image (x,y): %d,%d\n" % ( dims[0], dims[1] ))

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
      # ( (original_dims, transformed_dims) )
      # original_dims gets passed along unchanged for the ride
      # transformed_dims is transformed and must be of the form (int, int)
      yield (dims, dims)

      for y in range(0, dims[1]):
        # pixels is a byte array
        pixels = b''
        while len(pixels) < x_bytes:
          new_pixels = img.read( x_bytes - len(pixels) )
          pixels += new_pixels
          if len(new_pixels) == 0:
            x_bytes = -1
            pixels = []
            self.dbg("Uh oh: unexpected EOF!\n")
        if len(pixels) == x_bytes:
          if 0 == 1:
            repacked_pixels = b''
            for integer in unpack(unpack_bytes_str, pixels):
              repacked_pixels += pack("=I", integer)
            yield unpack( unpack_str, repacked_pixels )
          else:
            yield unpack( unpack_str, pixels )

    def getFakeData(self, dims):
      ''' Generate a fake dtm for fast testing of various other generator-wrappers '''
      self.dbg("generating fake test data (x,y): %d,%d\n" % ( dims[0], dims[1] ))
      yield (dims, dims)

      map_fun = lambda z: z*z*.0001
      for y in range(0, dims[1]):
        dtm_line = list(map(map_fun, list(range(y*dims[0],(y+1)*dims[0]))))
        yield dtm_line

    def getTestData0(self):
      ''' Generate 3x3 grid to test face generation '''
      self.dbg("generating 3x3 test grid\n")
      yield ( (9, 9), (9, 9) )

      ignr_val = self.__ignore_value
      def some_iter():
        for a in range(0,1000):
          yield a * 0.01
      it = some_iter()

      yield [ignr_val, ignr_val, next(it), next(it), next(it), next(it), next(it), ignr_val, ignr_val]
      yield [ignr_val, next(it), next(it), next(it), next(it), next(it), next(it), next(it), ignr_val]
      yield [ignr_val, next(it), next(it), next(it), next(it), next(it), next(it), next(it), ignr_val]

      yield [next(it), next(it), next(it), next(it), next(it), next(it), next(it), next(it), next(it)]
      yield [next(it), next(it), next(it), next(it), next(it), next(it), next(it), next(it), next(it)]
      yield [next(it), next(it), next(it), next(it), next(it), next(it), next(it), next(it), next(it)]

      yield [ignr_val, next(it), next(it), next(it), next(it), next(it), next(it), next(it), ignr_val]
      yield [ignr_val, next(it), next(it), next(it), next(it), next(it), next(it), next(it), ignr_val]
      yield [ignr_val, ignr_val, next(it), next(it), next(it), next(it), next(it), ignr_val, ignr_val]

    def normalize(self, image_iter, new_max = 10, new_min = 0, old_max_min = None):
      ''' takes a generator and normalizes the points between new_max and new_min
          you must pass old_max_min as (old_max, old_min)
          also removes points with value self.__ignore_value and replaces them with None
      '''

      if old_max_min == None:
        raise Exception("eep: need to know max/min values ahead of time to use normalization")
      # use the passed in values ...
      old_max = old_max_min[0]
      old_min = old_max_min[1]

      # calculate new range for dataset
      new_range = new_max - new_min

      # pass on dimensions since we don't modify them here
      yield next(image_iter)

      self.dbg("normalizing data...\n");

      #
      data_range = old_max - old_min
      self.dbg("min/max/range: " + str(old_min) + "/" + str(old_max) + "/" + str(data_range) + "\n")

      # map_fun = lambda point: (point - old_min)/data_range*new_range + new_min
      # closures rock!
      def normalize_fun(point):
        if point == self.__ignore_value:
          return None
        return (point - old_min)/data_range*new_range + new_min

      self.dbg("performing in-line normalization...\n")
      found_min = found_max = None
      for line in image_iter:
        yield list(map(normalize_fun, line))

      self.dbg("normalized all points to new range\n")

    def normalize_dtm(self, dtm_vals, new_max = 10, new_min = 0, old_max_min = None):
      ''' takes an entire dtm and normalizes the points between new_max and new_min
          optionally pass old_max_min as (old_max, old_min) to keep from iterating
          through the data twice
      '''

      # calculate new range for dataset
      new_range = new_max - new_min

      # use the passed in values ... or find them ourself
      try:
        old_max = old_max_min[0]
        old_min = old_max_min[1]
      except:
        self.dbg("finding max/min value in data...\n");
        old_max = old_min = dtm_vals[0]
        for val in dtm_vals:
          if old_max < val:
            old_max = val
          if old_min == self.__ignore_val or ( old_min > val and val != self.__ignore_val ):
            old_min = val

      self.dbg("normalizing data...\n");
      data_range = old_max - old_min
      self.dbg("min/max/range: " + str(old_min) + "/" + str(old_max) + "/" + str(data_range) + "\n")
      map_fun = lambda point: (point - old_min)/data_range*new_range + new_min
      self.dbg("performing normalization...\n")
      dtm_vals = list(map(map_fun, dtm_vals))
      self.dbg("normalized all points to new range\n")

      return dtm_vals

    def genMesh(self, image_iter):
      '''Generates/returns a mesh object from an image iterator
         this has the value-added feature that a value of "None" is ignored
      '''

      # Get the output image size given the above transforms
      (orig_dims, processed_dims) = next(image_iter)

      # Let's interpolate the binned DTM with blender -- yay meshes!
      coords = []
      faces  = []
      face_count = 0
      coord = -1
      max_x = processed_dims[0]
      max_y = processed_dims[1]

      line_count = 0
      current_line = []
      last_line = next(image_iter)
      point_offset = 0
      previous_point_offset = 0

      # Let's add any initial points that are appropriate
      x = 0
      point_offset += len( last_line ) - last_line.count(None)
      for z in last_line:
        if z != None:
          coords.extend([x*0.01, 0.0, z])
          coord += 1
        x += 1

      # We want to ignore points with a value of "None" but we also need to create vertices
      # with an index that we can re-create on the next line. The solution is to remember
      # two offsets: the point offset and the previous point offset.
      #   these offsets represent the point index that blender gets -- not the number of
      #   points we have read from the image

      # if "x" represents points that are "None" valued then conceptually this is how we
      # think of point indices:
      #
      # previous line: offset0   x   x  +1  +2  +3
      # current line:  offset1   x  +1  +2  +3   x

      # once we can map points we can worry about making triangular or square faces to fill
      # the space between vertices so that blender is more efficient at managing the final
      # structure.

      self.dbg('generate mesh coords/faces from processed image data...\n')

      # read each new line and generate coordinates+faces
      for dtm_line in image_iter:

        # Keep track of where we are in the image
        line_count += 1
        y_val = line_count*-0.01
        if line_count % 31 == 0:
          self.dbg("reading image... %d of %d\n" % ( line_count, processed_dims[1] ))

        # Just add all points blindly
        # TODO: turn this into a map
        x = 0
        for z in dtm_line:
          if z != None:
            coords.extend( [x*0.01, y_val, z] )
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
            faces.extend( [
              previous_point_offset,
              previous_point_offset+1,
              point_offset+1,
              point_offset,
              ] )
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

      self.dbg('generate mesh from coords/faces...\n')
      me = bpy.data.add_mesh('myMesh') # create a new mesh

      #      self.dbg("DBG - first face: %d, %d, %d, %d\n" % (
      #        faces[0],
      #        faces[1],
      #        faces[2],
      #        faces[3]
      #        ))
      #      self.dbg('DBG - removing faces for faster debugging and a point cloud...\n')
      #      faces = []
      #      face_count = 0
      #      faces = [0,1,7,6]
      #      face_count = 1

      self.dbg('coord: %d\n' % coord)
      self.dbg('len(coords): %d\n' % len(coords))
      self.dbg('len(faces): %d\n' % len(faces))
      # self.dbg('coords: %s\n' % " " + str(coords))
      # Add all coordinates/faces
      me.add_geometry(coord + 1, 0, face_count)
      self.dbg('setting coords...\n')
      me.verts.foreach_set("co", coords)
      self.dbg('setting faces...\n')
      me.faces.foreach_set("verts_raw", faces)
      self.dbg('running update...\n')
      me.update()

      return me

    ################################################################################
    #  Yay, done with helper functions ... let's see the abstraction in action!    #
    ################################################################################
    def execute(self, context):
      self.__ignore_value = unpack("f", pack("I", 0xFF7FFFFB))[0]

      # TODO: un-hardcode this image
      # img = open("/home/pirl/tims/Projects/Blender/PSP_001714_1415_PSP_001846_1415/1/DTEEC_001714_1415_001846_1415_U01.IMG", 'r')
      self.init_dbg()
      img = False
      if( 1 == 1 ):
        self.dbg('opening/importing file...\n')
        img = open("/home/pirl/tims/Projects/Blender/PSP_001714_1415_PSP_001846_1415/1/DTEEC_001714_1415_001846_1415_U01.IMG", 'rb')
        # img = open("/Users/imoverclocked/Blender/DTEEC_001714_1415_001846_1415_U01.IMG", 'rb')

        self.dbg('read PDS Label...\n')
        (label, parsedLabel) = self.getPDSLabel(img)

        self.dbg('parse PDS Label...\n')
        image_dims = self.getLinesAndSamples(parsedLabel)

        # TODO: un-hardcode this value (get it from PDS label -- if available)
        img_max_min_vals = (-1865.84, -2990.89)
        self.dbg('import/bin image data...\n')
        # (binned_dtm, processed_dims) = self.getBinnedImage(img, image_dims)
        # MAGIC VALUE? -- need to formalize this to rid ourselves of bad points
        img.seek(28)
        # Crop off 4 lines
        # img.seek(4*6227)

        # Get an iterator to iterate over lines
        image_iter = self.getImage(img, image_dims)

        # Manually implement hackish y-offset (DEBUG)
        # img.seek(4096*6227)
        # image_iter = self.cropXY(image_iter, YSize=2375, XSize=2375, XOffset=3300)

        # crop a portion of the image to speed things up
        # image_iter = self.cropXY(image_iter, YSize=5000)
        # image_iter = self.cropXY(image_iter, YSize=500, XSize=500, XOffset=1600, YOffset=1000)

      else:
        # image_iter = self.getFakeData( (100, 500) )
        # img_max_min_vals = (100*500, 0)
        image_iter = self.getTestData0()
        img_max_min_vals = (10, 0)


      ## Wrap the image_iter generator with other generators to modify the dtm on a
      ## line-by-line basis. This creates a stream of modifications instead of reading
      ## all of the data at once, processing all of the data (potentially several times)
      ## and then handing it off to blender
      ## TODO: find a way to utilize threading to take advantage of multiple cores
      ## TODO: find a way to alter projection based on transformations below

      ## bin these lines down via 6x6 sampling/averaging
      # image_iter = self.bin6(image_iter)
      image_iter = self.bin2(image_iter)

      # normalize points to fit between 0 .. 10
      image_iter = self.normalize(image_iter, old_max_min = img_max_min_vals)

      # Create a new mesh object and set data from the image iterator
      self.dbg('creating new object...\n')
      ob_new = bpy.data.add_object("MESH", "DTM")
      self.dbg('setting mesh data in new object...\n')
      ob_new.data = self.genMesh(image_iter)

      if img:
        img.close()

      # Add mesh object to the current scene
      scene = context.scene
      self.dbg('linking object to scene...\n')
      scene.objects.link(ob_new)
      scene.objects.active = ob_new
      ob_new.selected = True
      # This seems to be necessary right now (Blender 2.50 A1)
      # but may not be in the future
      bpy.ops.object.rotation_clear()

      self.dbg('aligning view to see whole of new object...\n');

      bpy.ops.view3d.view_all(center=True);
      bpy.ops.view3d.camera_to_view();

      self.dbg('done with ops ... now wait for blender...\n')

      return ('FINISHED',)

## How to register the script inside of Blender

# bpy.ops.add(ImportHiRISEIMGDTM)
# import  dynamic_menu
# menu_func = (lambda self, context: self.layout.operator(ImportHiRISEIMGDTM.bl_idname, text="import HiRISE DTM from PDS IMG"))
# menu_item = dynamic_menu.add(bpy.types.INFO_MT_mesh_add, menu_func)

def menu_func(self, context):
    text="import HiRISE DTM from PDS IMG"
    icon='PLUGIN'
    self.layout.operator(ImportHiRISEIMGDTM.bl_idname, text)
    # self.layout.operator(ImportHiRISEIMGDTM.bl_idname, text, icon)

def register():
    bpy.types.INFO_MT_file_import.append(menu_func)

def unregister():
    bpy.types.INFO_MT_file_import.append(menu_func)

register()
if __name__ == "__main__":
    # bpy.ops.mesh.mesh.ImportHiRISEIMGDTM()
    register()
