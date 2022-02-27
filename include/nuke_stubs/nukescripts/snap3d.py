# Copyright (c) 2010 The Foundry Visionmongers Ltd.  All Rights Reserved.

import math
import nuke
import _nukemath

#
# Predefined snapping functions.
#

# Lazy functions to call on "thisNode"
def translateThisNodeToPoints():
  return translateToPoints(nuke.thisNode())

def translateRotateThisNodeToPoints():
  return translateRotateToPoints(nuke.thisNode())

def translateRotateScaleThisNodeToPoints():
  return translateRotateScaleToPoints(nuke.thisNode())

# Lazy functions to determine the vertex selection
# These are the external user functions
# Much hard work is done in obtaining the selection in these functions
def translateToPoints(nodeToSnap):
  '''
  Translate the specified node to the average position of the current vertex selection in the active viewer.
  The nodeToSnap must contain a 'translate' knob and the transform order must be 'SRT'.

  @type nodeToSnap:   nuke.Node
  @param nodeToSnap:  Node to translate
  '''
  return translateSelectionToPoints(nodeToSnap, getSelection())

def translateRotateToPoints(nodeToSnap):
  '''
  Translate the specified node to the average position of the current vertex selection in the active viewer
  and rotate to the orientation of the (mean squares) best fit plane for the selection.
  The nodeToSnap must contain 'translate' and 'rotate' knobs, the transform order must be 'SRT' and the
  rotation order must be 'ZXY'.

  @type nodeToSnap:   nuke.Node
  @param nodeToSnap:  Node to translate and rotate
  '''
  return translateRotateSelectionToPoints(nodeToSnap, getSelection())

def translateRotateScaleToPoints(nodeToSnap):
  '''
  Translate the specified node to the average position of the current vertex selection in the active viewer,
  rotate to the orientation of the (mean squares) best fit plane for the selection
  and scale to the extents of the selection.
  The nodeToSnap must contain 'translate', 'rotate' and 'scale' knobs, the transform order must be 'SRT' and
  the rotation order must be 'ZXY'.

  @type nodeToSnap:   nuke.Node
  @param nodeToSnap:  Node to translate, rotate and scale
  '''
  return translateRotateScaleSelectionToPoints(nodeToSnap, getSelection())

# Verification wrappers
def translateSelectionToPoints(nodeToSnap, vertexSelection):
  try:
    verifyNodeToSnap(nodeToSnap, ["translate", "xform_order", "rot_order"])
    verifyVertexSelection(vertexSelection, 1)
    translateToPointsVerified(nodeToSnap, vertexSelection)
  except ValueError as e:
    nuke.message(str(e))

def translateRotateSelectionToPoints(nodeToSnap, vertexSelection):
  try:
    verifyNodeToSnap(nodeToSnap, ["translate", "rotate", "xform_order", "rot_order"])
    verifyVertexSelection(vertexSelection, 1)  # This can use the normal direction
    translateRotateToPointsVerified(nodeToSnap, vertexSelection)
  except ValueError as e:
    nuke.message(str(e))

def translateRotateScaleSelectionToPoints(nodeToSnap, vertexSelection):
  try:
    verifyNodeToSnap(nodeToSnap, ["translate", "rotate", "scaling", "xform_order", "rot_order"])
    verifyVertexSelection(vertexSelection, 3)
    translateRotateScaleToPointsVerified(nodeToSnap, vertexSelection)
  except ValueError as e:
    nuke.message(str(e))

def verifyVertexSelection(vertexSelection, minLen):
  if len(vertexSelection) < minLen:
    raise ValueError('Selection must be at least %d points' % minLen)

# Verification functions
def verifyNodeToSnap(nodeToSnap, knobList):
  # Check the knobs
  nodeKnobs = nodeToSnap.knobs()
  for knob in knobList:
    if knob not in nodeKnobs:
      raise ValueError('Snap requires "%s" knob' % knob)
  # Verify the transform order
  verifyNodeOrder(nodeToSnap, "xform_order", "SRT")
  # Verify the rotation order as necessary
  if "rotate" in knobList:
    verifyNodeOrder(nodeToSnap, "rot_order", "ZXY")

def verifyNodeOrder(node, knobName, orderName):
  orderKnob = node.knob(knobName)
  # Is there a better way than this?
  order = orderKnob.enumName( int(orderKnob.getValue()) )
  if orderName != order:
    raise ValueError('Snap requires "%s" %s' % (orderName, knobName))

# Info for each vertex
class VertexInfo:
  def __init__(self, objnum, index, value, position):
    self.objnum = objnum
    self.index = index
    self.value = value
    self.position = position  # This is updated on applying a transform

# Selection container
class VertexSelection:
  def __init__(self):
    self.vertexInfoSet = set()
    self.length = 0

  def __len__(self):
    return self.length

  # Convenience function to allow direct iteration
  def __iter__(self):
    # Since a set is not iterable use a generator function
    # Don't change the set while iterating!
    for info in self.vertexInfoSet:
      yield info

  def add(self, vertexInfo):
    self.vertexInfoSet.add(vertexInfo)
    self.length += 1

  def points(self):
    # Generate an iterable list of the positions
    points = []
    for info in self.vertexInfoSet:
      points += [info.position]
    return points

  def indices(self):
    # Generate a searchable dictionary of the positions
    indices = {}
    i = 0
    for info in self.vertexInfoSet:
      indices[info.index] = i
      i += 1
    return indices

  def translate(self, vector):
    for info in self.vertexInfoSet:
      info.position += vector

  def inverseRotate(self, vector, order):
    #nuke.tprint(vector)
    #nuke.tprint(order)
    # Create a rotation matrix
    m = _nukemath.Matrix3()
    m.makeIdentity()
    for axis in order:
      if axis == "X":
        # Apply X rotation
        m.rotateX(vector[0])
        #nuke.tprint("rotateX: %f" % vector[0])
      elif axis == "Y":
        # Apply Y rotation
        m.rotateY(vector[1])
        #nuke.tprint("rotateY: %f" % vector[1])
      elif axis == "Z":
        # Apply Z rotation
        m.rotateZ(vector[2])
        #nuke.tprint("rotateZ: %f" % vector[2])
      else:
        raise ValueError("Invalid rotation axis: %s" % axis)

    # Now determine the inverse/transpose matrix
    #nuke.tprint(m)
    transpose(m)
    #nuke.tprint(m)

    # Apply the matrix to the vertices
    for info in self.vertexInfoSet:
      info.position = m * info.position

  def scale(self, vector):
    for info in self.vertexInfoSet:
      info.position[0] *= vector[0]
      info.position[1] *= vector[1]
      info.position[2] *= vector[2]

# Helper function since Matrix3 has no transpose operation
def transpose(m):
  t = m[0+3*1]
  m[0+3*1] = m[1+3*0]
  m[1+3*0] = t

  t = m[0+3*2]
  m[0+3*2] = m[2+3*0]
  m[2+3*0] = t

  t = m[1+3*2]
  m[1+3*2] = m[2+3*1]
  m[2+3*1] = t

  return

# Core snapping functions
def translateToPointsVerified(nodeToSnap, vertexSelection):
  # Find the average position
  centre = calcAveragePosition(vertexSelection)
  # Move the nodeToSnap to the average position
  nodeToSnap['translate'].setValue(centre)
  # Subtract this translation from the vertexSelection
  inverseTranslation = -centre
  vertexSelection.translate(inverseTranslation)

def scaleToPointsVerified(nodeToScale, vertexSelection):
  # Scale the nodeToScale to fit the bounding box of the selected points
  scale = calcBounds(vertexSelection)
  nodeToScale['scaling'].setValue(scale)
  # Apply the inverse scale to the points
  inverseScale = _nukemath.Vector3(1/scale[0], 1/scale[1], 1/scale[2])
  vertexSelection.scale(inverseScale)

def rotateToPointsVerified(nodeToSnap, vertexSelection):
  # Get the normal of the points
  norm = averageNormal(vertexSelection)
  # Calculate the rotation vector
  rotationVec = calcRotationVector(vertexSelection, norm)
  # Convert to degrees
  rotationDegrees = _nukemath.Vector3( math.degrees(rotationVec.x), math.degrees(rotationVec.y), math.degrees(rotationVec.z) )
  # Set the node transform
  nodeToSnap['rotate'].setValue(rotationDegrees)
  # Apply the reverse rotation to the points
  vertexSelection.inverseRotate(rotationVec, "YXZ")

def translateRotateToPointsVerified(nodeToSnap, vertexSelection):
  # Note that the vertexSelection positions are updated as we go
  translateToPointsVerified(nodeToSnap, vertexSelection)
  rotateToPointsVerified(nodeToSnap, vertexSelection)

def translateRotateScaleToPointsVerified(nodeToSnap, vertexSelection):
  # Note that the vertexSelection positions are updated as we go
  translateRotateToPointsVerified(nodeToSnap, vertexSelection)
  scaleToPointsVerified(nodeToSnap, vertexSelection)

# Get the rotation vector
def calcRotationVector(vertexSelection, norm):
  # Collate a point set from the vertex selection
  points = vertexSelection.points()

  # Find a best fit plane with three or more points
  if len(vertexSelection) >= 3:
    planeTri = nuke.geo.bestFitPlane(*points)

    rotationVec = planeRotation(planeTri, norm)
  elif len(vertexSelection) == 2:
    # Choose the axes dependent on the line direction
    u = points[1] - points[0]
    u.normalize()

    w = norm
    v = w.cross(u)
    v.normalize()
    # Update w
    w = v.cross(u)

    # Fabricate a tri (tuple)
    planeTri = (_nukemath.Vector3(0.0, 0.0, 0.0), u, v)

    rotationVec = planeRotation(planeTri, norm)
  elif len(vertexSelection) == 1:
    # Choose the axes dependent on the normal direction
    w = norm
    w.normalize()

    if abs(w.x) < abs(w.y):
      v = _nukemath.Vector3(0.0, 1.0, 0.0)
      u = w.cross(v)
      u.normalize()
      # Update v
      v = w.cross(u)
    else:
      u = _nukemath.Vector3(1.0, 0.0, 0.0)
      v = w.cross(u)
      v.normalize()
      # Update v
      u = w.cross(v)

    # Fabricate a tri (tuple)
    planeTri = (_nukemath.Vector3(0.0, 0.0, 0.0), u, v)

    rotationVec = planeRotation(planeTri, norm)

    # In fact this only handles ZXY (see planeRotation)
    rotationVec.z = 0

  return rotationVec

#
# Geometric functions
#

def calcAveragePosition(vertexSelection):
  '''
  Calculate the average position of all points.

  @param points: An iterable sequence of _nukemath.Vector3 objects.
  @return: A _nukemath.Vector3 containing the average of all the points.
  '''
  pos = _nukemath.Vector3(0, 0, 0)
  count = 0
  for info in vertexSelection:
    point = info.position
    pos += point
    count += 1
  if count == 0:
    return
  pos /= count
  return pos

def calcBounds(vertexSelection):
  # Get the bounding box of all the selected points
  # Avoid zero size to allow inverse scaling (1/scale)
  high = _nukemath.Vector3(1e-20, 1e-20, 1e-20)
  low = _nukemath.Vector3(-1e-20, -1e-20, -1e-20)
  for info in vertexSelection:
    pos = info.position
    for i in range(len(pos)):
      if pos[i] < low[i]:
        low[i] = pos[i]
      elif pos[i] > high[i]:
        high[i] = pos[i]

  bounds = high - low
  return bounds

def planeRotation(tri, norm=None):
  '''
  Calculate the rotations around the X, Y and Z axes that will align a plane
  perpendicular to the Z axis with the given triangle.

  @param tri: A list or tuple of 3 _nukemath.Vector3 objects. The 3 points must
   describe the plane (i.e. they must not be collinear).
  @return: A _nukemath.Vector3 object where the x coordinate is the angle of
   rotation around the x axis and so on.
  @raise ValueError: if the three points are collinear.
  '''
  # Get the vectors along two edges of the triangle described by the three points.
  a = tri[1] - tri[0]
  b = tri[2] - tri[0]

  # Calculate the basis vectors for an orthonormal basis, where:
  # - u is parallel to a
  # - v is perpendicular to u and lies in the plane defined by a and b
  # - w is perpendicular to both u and v
  u = _nukemath.Vector3(a)
  u.normalize()
  w = a.cross(b)
  w.normalize()
  v = w.cross(u)

  # If a normal was passed in, check to make sure that the one we're generating
  # is aligned close to the same way
  if norm != None:
    if w.dot(norm) < 0.0:
      w.x = -w.x
      w.y = -w.y
      w.z = -w.z
      # Don't mirror!
      v.x = -v.x
      v.y = -v.y
      v.z = -v.z

  # Now find the rotation angles necessary to align a card to the uv plane.
  m = ( (u[0], v[0], w[0]),
        (u[1], v[1], w[1]),
        (u[2], v[2], w[2]) )
  if abs(m[1][2]) == 1.0:
    ry = 0.0
    rx = (math.pi / 2.0) * -m[1][2]
    rz = math.atan2(-m[0][1], m[0][0])
  else:
    cosx = math.sqrt(m[0][2] ** 2 + m[2][2] ** 2)
    if cosx == 0:
      cosx = 1.0
    rx = math.atan2(-m[1][2], cosx)
    rz = math.atan2(m[1][0] / cosx, m[1][1] / cosx)
    ry = math.atan2(m[0][2] / cosx, m[2][2] / cosx)

  return _nukemath.Vector3(rx, ry, rz)

#
# Helper functions
#
def averageNormal(vertexSelection):
  '''
  averageNormal(selectionThreshold -> _nukemath.Vector3
  Return a _nukemath.Vector3 which is the average of the normals of all selected points
  '''

  if not nuke.activeViewer():
    return None

  # Put the indices in a dictionary for fast searching
  fastIndices = vertexSelection.indices()

  found = False
  norm = _nukemath.Vector3(0.0, 0.0, 0.0)

  for theNode in allNodesWithGeoSelectKnob():
    geoSelectKnob = theNode['geo_select']
    sel = geoSelectKnob.getSelection()
    objs = geoSelectKnob.getGeometry()

    for o in range(len(sel)):
      objPrimitives = objs[o].primitives()
      objTransform = objs[o].transform()

      # Use a dictionary for fast searching
      visitedPrimitives = {}
      for prim in objPrimitives:
        # This will be slow!
        if prim not in visitedPrimitives:
          for pt in prim.points():
            # This will be slow!
            if pt in fastIndices:
              found = True
              n = prim.normal()
              n = _nukemath.Vector3(n[0], n[1], n[2])
              n = objTransform.vtransform(n)
              norm += n
              visitedPrimitives[prim] = pt
              break

  if found == False:
    return None

  norm.normalize()
  return norm


def anySelectedPoint(selectionThreshold=0.5):
  '''
  anySelectedPoint(selectionThreshold) -> _nukemath.Vector3
  Return a selected point from the active viewer or the first viewer with a selection.
  The selectionThreshold parameter is used when working with a soft selection.
  Only points with a selection level >= the selection threshold will be returned by this function.
  '''
  if not nuke.activeViewer():
    return None

  for n in allNodesWithGeoSelectKnob():
    geoSelectKnob = n['geo_select']
    sel = geoSelectKnob.getSelection()
    objs = geoSelectKnob.getGeometry()
    for o in range(len(sel)):
      objSelection = sel[o]
      for p in range(len(objSelection)):
        if objSelection[p] >= selectionThreshold:
          pos = objs[o].points()[p]
          tPos = objs[o].transform() * _nukemath.Vector4(pos.x, pos.y, pos.z, 1.0)
          return _nukemath.Vector3(tPos.x, tPos.y, tPos.z)
  return None


def selectedPoints(selectionThreshold=0.5):
  '''
  selectedPoints(selectionThreshold) -> iterator

  Return an iterator which yields the position of every point currently
  selected in the Viewer in turn.

  The selectionThreshold parameter is used when working with a soft selection.
  Only points with a selection level >= the selection threshold will be
  returned by this function.
  '''
  if not nuke.activeViewer():
    return

  for info in selectedVertexInfos(selectionThreshold):
    yield info.position


def getSelection(selectionThreshold=0.5):
  # Build a VertexSelection from VertexInfos
  vertexSelection = VertexSelection()
  for info in selectedVertexInfos(selectionThreshold):
    vertexSelection.add(info)
  return vertexSelection


def selectedVertexInfos(selectionThreshold=0.5):
  '''
  selectedVertexInfos(selectionThreshold) -> iterator

  Return an iterator which yields a tuple of the index and position of each
  point currently selected in the Viewer in turn.

  The selectionThreshold parameter is used when working with a soft selection.
  Only points with a selection level >= the selection threshold will be
  returned by this function.
  '''
  if not nuke.activeViewer():
    return

  for n in allNodesWithGeoSelectKnob():
    geoSelectKnob = n['geo_select']
    sel = geoSelectKnob.getSelection()
    objs = geoSelectKnob.getGeometry()
    for o in range(len(sel)):
      objSelection = sel[o]
      objPoints = objs[o].points()
      objTransform = objs[o].transform()
      for p in range(len(objSelection)):
        value = objSelection[p]
        if value >= selectionThreshold:
          pos = objPoints[p]
          tPos = objTransform * _nukemath.Vector4(pos.x, pos.y, pos.z, 1.0)
          yield VertexInfo(o, p, value, _nukemath.Vector3(tPos.x, tPos.y, tPos.z))


def anySelectedVertexInfo(selectionThreshold=0.5):
  '''
  anySelectedVertexInfo(selectionThreshold) -> VertexInfo

  Returns a single VertexInfo for a selected point. If more than one point is
  selected, one of them will be chosen arbitrarily.

  The selectionThreshold parameter is used when working with a soft selection.
  Only points with a selection level >= the selection threshold will be
  returned by this function.
  '''
  if not nuke.activeViewer():
    return None

  for n in allNodesWithGeoSelectKnob():
    geoSelectKnob = n['geo_select']
    sel = geoSelectKnob.getSelection()
    objs = geoSelectKnob.getGeometry()
    for o in range(len(sel)):
      objSelection = sel[o]
      objPoints = objs[o].points()
      objTransform = objs[o].transform()
      for p in range(len(objSelection)):
        value = objSelection[p]
        if value >= selectionThreshold:
          pos = objPoints[p]
          tPos = objTransform * _nukemath.Vector4(pos.x, pos.y, pos.z, 1.0)
          return VertexInfo(o, p, value, _nukemath.Vector3(tPos.x, tPos.y, tPos.z))
  return None


def allNodes(node = nuke.root()):
  '''
  allNodes() -> iterator
  Return an iterator which yields all nodes in the current script.

  This includes nodes inside groups. They will be returned in top-down,
  depth-first order.
  '''
  yield node
  if hasattr(node, "nodes"):
    for child in node.nodes():
      for n in allNodes(child):
        yield n


def allNodesWithGeoSelectKnob():
  if nuke.activeViewer():
    preferred_nodes = [n for n in nuke.activeViewer().getGeometryNodes() if 'geo_select' in n.knobs()]
  else:
    preferred_nodes = []
  nodes = preferred_nodes + [n for n in allNodes() if 'geo_select' in n.knobs() and n not in preferred_nodes]
  return nodes


def cameraProjectionMatrix(cameraNode):
  'Calculate the projection matrix for the camera based on its knob values.'

  # Matrix to transform points into camera-relative coords.
  camTransform = cameraNode['transform'].value().inverse()

  # Matrix to take the camera projection knobs into account
  roll = float(cameraNode['winroll'].getValue())
  scale_x, scale_y = [float(v) for v in cameraNode['win_scale'].getValue()]
  translate_x, translate_y = [float(v) for v in cameraNode['win_translate'].getValue()]
  m = _nukemath.Matrix4()
  m.makeIdentity()
  m.rotateZ(math.radians(roll))
  m.scale(1.0 / scale_x, 1.0 / scale_y, 1.0)
  m.translate(-translate_x, -translate_y, 0.0)

  # Projection matrix based on the focal length, aperture and clipping planes of the camera
  focal_length = float(cameraNode['focal'].getValue())
  h_aperture = float(cameraNode['haperture'].getValue())
  near = float(cameraNode['near'].getValue())
  far = float(cameraNode['far'].getValue())
  projection_mode = int(cameraNode['projection_mode'].getValue())
  p = _nukemath.Matrix4()
  p.projection(focal_length / h_aperture, near, far, projection_mode == 0)

  # Matrix to translate the projected points into normalised pixel coords
  format = nuke.root()['format'].value()
  imageAspect = float(format.height()) / float(format.width())
  t = _nukemath.Matrix4()
  t.makeIdentity()
  t.translate( 1.0, 1.0 - (1.0 - imageAspect / float(format.pixelAspect())), 0.0 )

  # Matrix to scale normalised pixel coords into actual pixel coords.
  x_scale = float(format.width()) / 2.0
  y_scale = x_scale * format.pixelAspect()
  s = _nukemath.Matrix4()
  s.makeIdentity()
  s.scale(x_scale, y_scale, 1.0)

  # The projection matrix transforms points into camera coords, modifies based
  # on the camera knob values, projects points into clip coords, translates the
  # clip coords so that they lie in the range 0,0 - 2,2 instead of -1,-1 - 1,1,
  # then scales the clip coords to proper pixel coords.
  return s * t * p * m * camTransform


def projectPoints(camera=None, points=None):
  '''
  projectPoint(camera, points) -> list of nuke.math.Vector2

  Project the given 3D point through the camera to get 2D pixel coordinates.

  @param camera: The Camera node or name of the Camera node to use for projecting
                 the point.
  @param points: A list or tuple of either nuke.math.Vector3 or of list/tuples of
                 three float values representing the 3D points.
  @raise ValueError: If camera or point is invalid.
  '''

  camNode = None
  if isinstance(camera, nuke.Node):
    camNode = camera
  elif isinstance(camera, str):
    camNode = nuke.toNode(camera)
  else:
    raise ValueError("Argument camera must be a node or the name of a node.")

  camMatrix = cameraProjectionMatrix(camNode)
  if camMatrix == None:
    raise RuntimeError("snap3d.cameraProjectionMatrix() returned None for camera.")

  if not ( isinstance(points, list) or isinstance(points, tuple) ):
    raise ValueError("Argument points must be a list or tuple.")

  for point in points:
    # Would be nice to not do this for every item but since lists/tuples can
    # containg anything...
    if isinstance(point, nuke.math.Vector3):
        pt = point
    elif isinstance(point, list) or isinstance(point, tuple):
      pt = nuke.math.Vector3(point[0], point[1], point[2])
    else:
      raise ValueError("All items in points must be nuke.math.Vector3 or list/tuple of 3 floats.")

    tPos = camMatrix * nuke.math.Vector4(pt.x, pt.y, pt.z, 1.0)
    yield nuke.math.Vector2(tPos.x / tPos.w, tPos.y / tPos.w)



def projectPoint(camera=None, point=None):
  '''
  projectPoint(camera, point) -> nuke.math.Vector2

  Project the given 3D point through the camera to get 2D pixel coordinates.

  @param camera: The Camera node or name of the Camera node to use for projecting
                 the point.
  @param point: A nuke.math.Vector3 or of list/tuple of three float values
                representing the 3D point.
  @raise ValueError: If camera or point is invalid.
  '''

  return next(projectPoints( camera, (point,) ))



def projectSelectedPoints(cameraName='Camera1'):
  '''
  projectSelectedPoints(cameraName='Camera1') -> iterator yielding nuke.math.Vector2

  Using the specified camera, project all of the selected points into 2D pixel
  coordinates and return their locations.

  @param cameraName: Optional name of the Camera node to use for projecting the
                     points. If omitted, will look for a node called Camera1.
  '''
  camNode = nuke.toNode(cameraName)
  camMatrix = cameraProjectionMatrix(camNode)
  for pt in selectedPoints():
    tPos = camMatrix * nuke.math.Vector4(pt.x, pt.y, pt.z, 1.0)
    yield nuke.math.Vector2(tPos.x / tPos.w, tPos.y / tPos.w)


#
# Managing the list of snapping functions.
#

# The list of snapping functions. Treat this as a read-only variable; if you
# want to add a new snapping function call addSnapFunc (below)
snapFuncs = []


def addSnapFunc(label, func):
  '''
  addSnapFunc(label, func) -> None
  Add a new snapping function to the list.

  The label parameter is the text that will appear in (eg.) an Enumeration_Knob
  for the function. It cannot be the same as any existing snap function label
  (if it is, the function will abort without changing anything).

  The func parameter is the snapping function. It must be a callable object
  taking a single parameter: the node to perform the snapping on.
  '''
  if label in dict(snapFuncs):
    return
  snapFuncs.append( (label, func) )


def callSnapFunc(nodeToSnap=None):
  '''
  callSnapFunc(nodeToSnap) -> None
  Call the snapping function on a node.

  The nodeToSnap parameter is optional. If it's not specified, or is None, we
  use the result of nuke.thisNode() instead.

  The node must have an Enumeration_Knob called "snapFunc" which selects the
  snapping function to call.
  '''
  if nodeToSnap is None:
    nodeToSnap = nuke.thisNode()

  # Make sure that the nodeToSnap has a snapFunc knob
  if "snapFunc" not in nodeToSnap.knobs():
    # TODO: warn the user that we can't snap this node.
    return

  snapFunc = dict(snapFuncs)[nodeToSnap['snapFunc'].value()]
  snapFunc(nodeToSnap)
