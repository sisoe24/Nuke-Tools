# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import os.path
import subprocess
import collections
import re
import math
import hiero.core


def fixPathForNuke(path):
  """ Clean up a path to be used in a file knob. """
  # Check for null/empty string
  if not path:
    return path

  # Nuke always treats '#' as placeholders for the frame number unless it's
  # escaped with a preceding '%'. Add the escaping.
  base, ext = os.path.splitext(path)
  paddingRegex = '#+$'
  match = re.search(paddingRegex, base)
  if match:
    base, padding = base[:match.start()], base[match.start():]
  else:
    padding = ''
  base = base.replace('#', '%#')
  path = base + padding + ext

  # Make sure that backslashes in paths (from Windows) don't get interpreted
  # as tab characters and such in Nuke
  path = path.replace("\\", "/")
  return path


class DefaultNodeKnobFormatter:
  def serialize(self, serializer, nodeType, knobValues, userKnobs, rawKnobs):
    serializer.serializeNode(nodeType, knobValues, userKnobs, rawKnobs)
  

class ReadNodeKnobFormatter:
  def serialize(self, serializer, nodeType, knobValues, userKnobs, rawKnobs):
    # do the inputs, then file, then format string, then first frame, then last frame
    inputs = 0
    file = ""
    format = ""
    first = 0
    last = 0
    auto_alpha = "true"
    
    # pull out all of the special knobs that we care about
    # putting the rest into another list
    remainingKnobs = {}
    for (key, value) in knobValues.items():
      if key == "file":
        file = value
      elif key == "format":
        format = value
      elif key == "first":
        first = value
      elif key == "last":
        last = value
      elif key == "inputs":
        inputs = value
      elif key == "auto_alpha":
        auto_alpha = value
      else:
        remainingKnobs[key] = value

    serializer.beginSerializeNode(nodeType)
    
    # write out the special knobs first
    serializer.serializeKnob("inputs", 0)
    serializer.serializeKnob("file", file)
    serializer.serializeKnob("format", format)
    serializer.serializeKnob("first", first)
    serializer.serializeKnob("last", last)
    serializer.serializeKnob("auto_alpha", auto_alpha)
    
    # write out the rest of the knobs
    serializer.serializeUserKnobs(userKnobs)
    serializer.serializeKnobs(remainingKnobs)
    serializer.serializeRawKnobs(rawKnobs)
    
    serializer.endSerializeNode()


class WriteNodeKnobFormatter:
  def serialize(self, serializer, nodeType, knobValues, userKnobs, rawKnobs):

    serializer.serializeUserKnobs(userKnobs)
    serializer.serializeRawKnobs(rawKnobs)

    priorityKnobs = ("file", "file_type",)
    #As knobs are stored as tags in the xml, they can't contain spaces in the
    #exporter code but their original name in nuke might contain them.
    #Use this map to map the exporter knob names to nuke knob names
    #TODO: obsolete knob name containing spaces and change the way in which
    #knobs are serialized in the export structure
    mappedKnobs = {"standard_layer_name_format" :"\"standard layer name format\"" }

    serializer.beginSerializeNode(nodeType)
    for knobKey in priorityKnobs:
      if knobKey in knobValues:
        serializer.serializeKnob(knobKey, knobValues[knobKey])
      
    for knobKey in list(knobValues.keys()):
      if knobKey not in priorityKnobs:
        serializer.serializeKnob(mappedKnobs[knobKey] if knobKey in list(mappedKnobs.keys()) else knobKey, knobValues[knobKey])

    serializer.endSerializeNode()
  

# special case serialization nodes
_customKnobFormatters = {"Read": ReadNodeKnobFormatter(), "Write": WriteNodeKnobFormatter()}

def RegisterCustomNukeKnobFormatter(nodeType, nodeKnobFormatter):
  _customKnobFormatters[nodeType] = nodeKnobFormatter


class Node(object):
  """ Base class for objects which represent elements in the written Nuke script.  Note that not all Node
      objects are actually nodes, some are just used to insert tcl commands into the script. """
  USER_KNOB_TYPE_TAB = 20
  USER_KNOB_TYPE_FILENAME = 2
  USER_KNOB_TYPE_INPUTTEXT = 1
  USER_KNOB_TYPE_CHECKBOX = 6
  
  # Specify which direction this Node will align with its AlignTo node (if any)
  kNodeAlignX = 0
  kNodeAlignY = 1

  def __init__(self, nodeType, inputNode0=None, inputNodes=None, **keywords):
    
    self._userKnobs = []
    self._rawKnobs = []

    if inputNodes == None:
      self._inputNodes = {}
    else:
      self._inputNodes = inputNodes.copy()
      
    # allow a single node to be passed in
    if inputNode0 != None:
      self._inputNodes[0] = inputNode0
      
    self._nodeType = nodeType
    self._knobValues = {}
    for (kw, value) in keywords.items():
      self._knobValues[kw] = value

    # Node to align to in the layout
    self._alignToNode = None
    self._nodeAlignment = self.kNodeAlignY

    # Vertical spacing to add above this node in its layout
    self._topSpacing = 0

    # Additional offset to add space between this Node and its AlignTo Node.
    self._alignmentOffsetX = 0
    self._alignmentOffsetY = 0

    # Ranges over which the knob is enabled. Most Nodes will be either
    # fully enabled or disabled, but some will have there disable knob
    # animated over time (e.g. Merge, Dissolve)
    self._enabledRanges = []

  def isNode(self):
    """ Check if this is actually a node, as opposed to a tcl command.  This default implementation
        looks at the node type string, if it starts with an upper case character it's treated as a node. """
    if len(self._nodeType) > 0 and self._nodeType[0].islower():
      return False
    else:
      return True
      
  def setKnob(self, knobName, knobValue):
    """ Set a knob value. """
    self._knobValues[str(knobName)] = knobValue
    
  def _addUserKnob(self, type, knobName, text=None, tooltip=None, value=None, visible=True):
    """ Helper function for adding user knobs. """
    self._userKnobs.append((type, knobName, text, tooltip, value, visible))
    
  def addTabKnob(self, knobName, text=None, tooltip=None):
    """ Add a tab knob. """
    self._addUserKnob(Node.USER_KNOB_TYPE_TAB, knobName, text)
    
  def addFilenameKnob(self, knobName, text=None, tooltip=None, value=None, visible=True):
    """ Add a filename knob. """
    self._addUserKnob(Node.USER_KNOB_TYPE_FILENAME, knobName, text, tooltip, value, visible)
    
  def addInputTextKnob(self, knobName, text=None, tooltip=None, value=None, visible=True):
    """ Add an input text knob. """
    self._addUserKnob(Node.USER_KNOB_TYPE_INPUTTEXT, knobName, text, tooltip, value, visible)

  def addCheckboxKnob(self, knobName, text=None, tooltip=None, value=False, visible=True):
    """ Add a checkbox knob. """
    self._addUserKnob(Node.USER_KNOB_TYPE_CHECKBOX, knobName, text, tooltip, value, visible)

  def addRawKnob(self, text):
    """ Add raw knob text to the node.  This is written directly to the script with no formatting. """
    self._rawKnobs.append( text )
    
  def knob(self, knobName):
    """ Get a knob value.  An exception is raised if no knob of that name exists. """
    return self._knobValues[str(knobName)]

  def knobs(self):
    """ Get a dict with all the node's knobs. """
    return self._knobValues

  def serialize(self, serializer):
    """ Serialize the node to the given serializer object. """
    if self._nodeType in _customKnobFormatters:
      knobFormatter = _customKnobFormatters[self._nodeType]
    else:
      knobFormatter = DefaultNodeKnobFormatter()
    
    return knobFormatter.serialize(serializer, self._nodeType, self._knobValues, self._userKnobs, self._rawKnobs)
  
  def formatString(self, width, height, pixelAspect=None):
    """ Helper function for creating a format string. """
    if pixelAspect is not None:
      return "%i %i 0 0 %i %i %f" % (width, height, width, height, pixelAspect)
    return str(width) + " " + str(height)
    
  def setName(self, name):
    """ Set the node name. """
    self.setKnob( 'name', name.replace(' ', '_') )
  
  def type(self):
    """ Get the node type. """
    return self._nodeType
      
  def setInputNode(self, index, node):
    self._inputNodes[index] = node
    
  def inputNodes(self):
    return self._inputNodes


  def getNodeSize(self):
    """ Get the size of the node.  This is an estimate, since in Nuke the size can be affected by
        the font size (and possibly other factors), but it works in most cases for layout of scripts. """
    if self.isNode():
      return 80, 20
    else:
      return 0, 0


  def setPosition(self, xpos, ypos):
    """ Set the xpos and ypos knobs for the node position. """
    self.setKnob('xpos', xpos)
    self.setKnob('ypos', ypos)


  def getPosition(self):
    """ Try to get the position of the node if it's been set, otherwise returns None, None. """
    try:
      return self.knob('xpos'), self.knob('ypos')
    except:
      return None, None


  def setAlignToNode(self, node, alignment = kNodeAlignY):
    """ Set the node to align this one to when the script is laid out. """
    self._alignToNode = node
    self._nodeAlignment = alignment

  def addEnabledRange(self, startRange, endRange, firstCompFrame):
    """ Add a Range of KeyFrames for which the Node is enabled. """

    # First add in the new range. Add 1 to the end time, since this is
    # the last frame we want the knob to be enabled, so it should be 
    # disabled on the following frame
    self._enabledRanges.append((startRange, endRange + 1))
  
    # Sort by start time

    getKey = lambda x: x[0]

    self._enabledRanges = sorted(self._enabledRanges, key=getKey)

    # Now we need to merge any ranges that overlap. Go through 
    # each range, and merge with any successive range where
    # the start time is less than the current end time
    numRanges = len(self._enabledRanges)
    currentRange = 0
  
    newRanges = []

    while (currentRange < numRanges):
      # Get the current range
      rangeStart, rangeEnd = self._enabledRanges[currentRange]

      nextRange = currentRange + 1

      # Loop until we find one that doesn't overlap	
      while (nextRange < numRanges) and (self._enabledRanges[nextRange][0] <= rangeEnd):
        rangeEnd = max(rangeEnd, self._enabledRanges[nextRange][1])
        nextRange += 1

      newRanges.append((rangeStart, rangeEnd))
      currentRange = nextRange

    self._enabledRanges = newRanges

    # Write into the knob string, making sure we disable the Node at the start
    knobString = "{{curve K x%s 1" % firstCompFrame

    for start, end in self._enabledRanges:
      knobString = knobString + " x%s %s x%s %s" % (start, 0, end, 1)
  
    self._knobValues["disable"] =  knobString + "}}"

  def setAlignmentOffset(self, alignmentOffsetX, alignmentOffsetY):
    """ Set an offset to add space between this Node and its AlignTo Node. """
    self._alignmentOffsetX = alignmentOffsetX
    self._alignmentOffsetY = alignmentOffsetY

  def getAlignmentOffsetX(self):
    """ Get the X alignment offset. """
    return self._alignmentOffsetX

  def getAlignmentOffsetY(self):
    """ Get the Y alignment offset. """
    return self._alignmentOffsetY

  def getAlignToNode(self):
    """ Get the node to align this one to when the script is laid out. """
    return self._alignToNode

  def getNodeAlignment(self):  
    """ Get the Alignment direction between this Node and its AlignTo Node. """
    return self._nodeAlignment
  
  def getTopSpacing(self):
    """ Get the spacing that will be added to the Node's top position. """
    return self._topSpacing

class PostageStampNode(Node):
  def __init__(self):
    Node.__init__(self, "PostageStamp", postage_stamp="true", hide_input = "true")

    self._topSpacing = 13

  def getNodeSize(self):
    """ Get the size of the node.  This is an estimate, since in Nuke the size can be affected by
        the font size (and possibly other factors), but it works in most cases for layout of scripts. """
    return 80, 64

class ReadNode(Node):
  def __init__(self,
               filePath,
               width=None,
               height=None,
               pixelAspect=None,
               firstFrame=None,
               lastFrame=None):
    filePath = fixPathForNuke(filePath)
    Node.__init__(self, "Read", file=filePath)
    if ((width != None) and (height != None)):
      if pixelAspect != None:
        self.setKnob("format", self.formatString(width, height, pixelAspect))
      else:
        self.setKnob("format", self.formatString(width, height))
    if (firstFrame != None):
      self.setKnob("first", firstFrame)
    if (lastFrame != None):
      self.setKnob("last", lastFrame)
    self._file = filePath
    # Default Read nodes to generate like Hiero clips.
    self.setKnob('before', 'black')
    self.setKnob('after',  'black')

  def getNodeSize(self):
    """ Get the size of the node.  This is an estimate, since in Nuke the size can be affected by
        the font size (and possibly other factors), but it works in most cases for layout of scripts. """
    return 80, 90



class PrecompNode(Node):
  def __init__(self, filePath, **knobs ):
    filePath = fixPathForNuke(filePath)
    Node.__init__(self, "Precomp", file=filePath, inputs=0, **knobs)
    self._file = filePath



class CompositeNode(Node):
  def __init__(self, nodeType, inputNode0=None, inputNodes=None, **keywords):
    Node.__init__(self, nodeType, inputNode0=inputNode0, inputNodes=inputNodes, **keywords)
    self._nodes = []


  def getNodes(self):
    # returning a copy of the list so clients don't accidently modify this one
    return self._nodes[:]


  def addNode(self, node):
    self._nodes.append(node)
    

  def serialize(self, serializer):
    for node in self._nodes:
      node.serialize(serializer) 
      
    Node.serialize(self, serializer)
    pass



class WriteNode(CompositeNode):
  def __init__(self, filePath, inputNode=None):
    filePath = fixPathForNuke(filePath)
    CompositeNode.__init__(self, "Write", inputNode0=inputNode, file=filePath)
    # Change _knobValues to be a OrderedDict so the order in which knob values
    # are added is retained. This is so that when written to script the knob
    # ordering is maintained. When reading a script the order that values are
    # read in can change the state of the created node.
    # TODO _knobValues should potentially be an OrderedDict in the Node base
    # class as the order of the knobs can matter for all nodes. However,
    # limiting the scope of this change to reduce the potential for unforeseen
    # consequences. Ideally we would use to_script for the write nodes, where we
    # get the knob values from an intermediate write node, and write the output
    # of that into the export script.
    self._knobValues = collections.OrderedDict(self._knobValues)

  def getNodeSize(self):
    """ Get the size of the node.  This is an estimate, since in Nuke the size can be affected by
        the font size (and possibly other factors), but it works in most cases for layout of scripts. """
    return 80, 44



class AddTimeCodeNode(Node):
  def __init__(self, timecodeStart, fps, dropFrames, frame=None, metafps=False, inputs=None, inputNode=None):
    '''timecodeStart should be a time (frame) value, fps should be a TimeBase object, and dropFrames should be true or false'''
    
    # validate that this works
    if dropFrames and not fps.supportsDropFrames():
      raise Exception("Adding a time code with drop frames enabled, but the fps (%f) does not support drop frames (meaning it's not 29.97 or 59.94)" % fps.toFloat())
      
    # Fairly complicated about the fps value
    # Nuke 6.3v8 and lower don't handle floating point fps and truncate to int, and don't round the value on load
    # so to make the time code generation work properly, we round the value to int before setting it in the script
    # Which would cause a rounded int fps to be output from the nuke script, except that code in the exporter actually puts in a ModifyMetadata node
    # after this AddTimeCode node that fixes the fps value.
    # If the user has requested a drop frame format, the fps needs to be float to tell Nuke 7.0 and greater to handle the time code as a drop frame
    # So we assume that the ModifyMetaData node is added after the AddTimeCodeNode to fix the fps to a float value in the metadata output,
    # and only send out a float frame rate when we have to. Because the AddTimeCode node calculations will all be on rounded ints anyways.
    
    fpsKnobValue = fps.toInt()
    if dropFrames and fps.supportsDropFrames():
      startcode = hiero.core.Timecode.timeToString(timecodeStart, fps, hiero.core.Timecode.kDisplayDropFrameTimecode)
      fpsKnobValue = fps.toFloat()
    else:
      startcode = hiero.core.Timecode.timeToString(timecodeStart, fps, hiero.core.Timecode.kDisplayTimecode)
    
    useFrame = "false"
    if frame is not None:
      useFrame = "true"
    else:
      frame = 0
      
    if not metafps:
      metafps = "false"
    else:
      metafps = "true"
      
    Node.__init__(self, "AddTimeCode", startcode=startcode, frame=frame, metafps=metafps, useFrame=useFrame, fps=fpsKnobValue, inputNode0=inputNode)



class AppendClipNode(Node):
  def __init__(self, inputs, inputNode=None, **kwargs):
    Node.__init__(self, "AppendClip", inputNode0=inputNode, inputs=inputs, meta_from_first="false", **kwargs)


    
class SetNode(Node):
  """ Not really a node, this adds a set command to the script. """
  def __init__(self, var, stack):
    Node.__init__(self, "set")
    self._var = var
    self._stack = stack

  def isNode(self):
    return False

  def serialize(self, serializer):
    serializer._nodeOutput = "set %s [stack %s]\n" % (str(self._var), str(self._stack))
    

    
class PushNode(Node):
  """ Not really a node, this adds a push command to the script. """

  def __init__(self, var):
    Node.__init__(self, "push")
    self._var = str(var)

  def isNode(self):
    return False
    
  def serialize(self, serializer):
    # Special case: push 0 is used for a disconnected input
    if self._var == '0':
      serializer._nodeOutput = "push 0\n"
    else:
      serializer._nodeOutput = "push $%s\n" % self._var


class UserDefinedNode (Node):
  """ Node which can be used to insert node text into the script. """

  def __init__(self, data):
    Node.__init__(self, "")
    assert isinstance(data, str) and data, "unexpected data %s '%s'" % (type(data), data)

    # Split into lines, so extra knobs can be inserted. If any further
    # functionality is added here it would probably be sensible to properly
    # parse the string as TCL script
    self._lines = data.splitlines()

    # Check for the whole thing being on one line, e.g. 'Blur {}' which might
    # happen when the user types into the additional knobs dialog. Need to split
    # the braces onto separate lines so knobs can be added
    if len(self._lines) == 1:
      line = self._lines[0]
      closeBraceIdx = line.rfind("}")
      self._lines = [line[:closeBraceIdx], line[closeBraceIdx:]]

    self._position = (None, None)


  def isNode(self):
    """ Assume that this actually is a node. """
    return True

  def setKnob(self, knobName, knobValue):
    """ Set a knob value. """
    self._lines.insert(1, "%s %s" %(knobName, knobValue))

  def setPosition(self, xpos, ypos):
    """ Override.  This class does not use the Node knobs dictionary, since it just has raw tcl script
        which is inserted into the output.  This inserts xpos and ypos knob lines into the script. """
    self._position = (xpos, ypos)

    # If we already have an xpos and ypos entry, we want to replace them. First remove the old ones
    # from the list
    newlines = []
    for line in self._lines:
      if not line.startswith("xpos ") and not line.startswith("ypos "):
        newlines.append(line)
    
    # Now insert the new xpos, ypos entries
    newlines.insert(1, "ypos %s" % ypos)
    newlines.insert(1, "xpos %s" % xpos)
    self._lines = newlines


  def getPosition(self):
    """ Override.  The base class relies on the xpos and ypos knobs being inserted into the _knobValues dict.
        This class doesn't use that, so the position is stored separately.  Return it. """
    return self._position


  def serialize(self, serializer):
    serializer._nodeOutput = "\n".join(self._lines) + "\n"



class GroupNode(CompositeNode):
  def __init__(self, name, **kwargs):
    CompositeNode.__init__(self, "Group", name=name, **kwargs)
    
  def serialize(self, serializer):
    output = ""
    
    Node.serialize(self, serializer)
    output += serializer._nodeOutput
    serializer._nodeOutput = ""    
    
    for node in self._nodes:
      node.serialize(serializer)
      output += serializer._nodeOutput
      serializer._nodeOutput = ""
      
    # End Group
    serializer._nodeOutput = output + "\nend_group\n"



class MergeNode(Node):
  def __init__(self, inputs, inputNodes=None):

    # If we are connecting the A input to the mask input also, we will
    # use dot nodes to tidy up the layout. Store them for processing
    # once the Mege node has been positioned.
    self._dotAInput = None
    self._dotMaskInput = None

    Node.__init__(self, "Merge2", inputNodes=inputNodes, inputs=inputs, metainput="All", operation="over", also_merge="all")

  def __init__(self, inputNodes=None):
    self._dotAInput = None
    self._dotMaskInput = None
    Node.__init__(self, "Merge2", inputs=2, metainput="All", operation="over", also_merge="all")

  def setDotInputs(self, dotAInput = None, dotMaskInput = None):
    self._dotAInput = dotAInput
    self._dotMaskInput = dotMaskInput

  def layoutDotInputs(self):
    xpos, ypos = self.getPosition()
    mergew, mergeh = self.getNodeSize()

    if self._dotAInput is not None:
      # Align A to the left of the Merge
      dotw, doth = self._dotAInput.getNodeSize()

      self._dotAInput.setPosition(xpos - 50, ypos + mergeh/2 - doth/2)

    if self._dotMaskInput is not None:
      # Align mask up and to the left of the Merge
      dotw, doth = self._dotMaskInput.getNodeSize()

      self._dotMaskInput.setPosition(xpos - 50, ypos + mergeh/2 - doth/2 - 50)

  def getNodeSize(self):
    """ Get the size of the node.  This is an estimate, since in Nuke the size can be affected by
        the font size (and possibly other factors), but it works in most cases for layout of scripts. """
    if 'label' in self._knobValues:
      # The node is bigger if it has a non-default label
      return 80, 32

    return 80, 20

class AddChannelsNode(Node):
  def __init__(self):
    Node.__init__(self, "AddChannels")

class AddLayerCommand(Node):
  """ This class doesn't represent a Nuke Node, instead it injects add_layer commands into
  the script. Since these have similar formatting to Nodes, this is enough to achieve this
  """
  def __init__(self):
    Node.__init__(self, "add_layer")

class TimeOffsetNode(Node):
  def __init__(self, offset):
    Node.__init__(self, "TimeOffset")

    # The time_offset knob stores ints. To store non-integer offsets, we can use
    # the hidden dtime_offset, which is added to time_offset inside the node, so
    # split the offset into the int and fractional parts and set both knobs.
    # This is imperfect because dtime_offset is a hidden knob, so if the user
    # opens the script in the DAG they will only see the integer offset, but
    # fixing this properly would require modifying the node.
    fractpart, intpart = math.modf(offset)
    self.setKnob("time_offset", int(intpart))
    if fractpart:
      self.setKnob("dtime_offset", fractpart)


class CopyNode(Node):
  def __init__(self, inputNodes=None):
    Node.__init__(self, "Copy", inputs=2, metainput="All", channels="all")


class RetimeNode(Node):
  def __init__(self, src_start, src_end, dst_start, dst_end, reverse=False):
    """Build a Nuke Retime node. Note that before/after are defaulted to "black" to
    mimic the way clips in Hiero are empty outside their defined range."""
    Node.__init__(self, "Retime", before="black", after="black")
    self.setKnob("input.first_lock", "true")
    self.setKnob("input.last_lock", "true")
    self.setKnob("output.first_lock", "true")
    self.setKnob("output.last_lock", "true")
    
    self.setKnob("input.first", src_start)
    self.setKnob("input.last", src_end)
    self.setKnob("output.first", dst_start)
    self.setKnob("output.last", dst_end)
    if reverse:
      self.setKnob("reverse", "true")



class ReformatNode(Node):
  kDisabled = "disabled"
  kToFormat = "to format"
  kToScale = "scale"
  kToBox = "to box"
  kResizeNone = "none"
  kResizeWidth = "width"
  kResizeHeight = "height"
  kResizeFit = "fit"
  kResizeFill = "fill"
  kResizeDistort = "distort"

  kToScaleLabel = "To Scale"
  kCustomLabel = "Custom"
  # Create comp reformating options
  kCompFormatAsPlate = "Plate Resolution"
  kCompReformatToSequence = "To Sequence Resolution"
  kCompReformatToFormat = "Custom"



  def __init__(self, resize=kResizeWidth, center=True, flip=False, flop=False, turn=False, to_type=kToFormat, format=None, scale=None, filter=None, box=None, pbb=False, black_outside=True):
    """Build a Nuke Reformat node.
    Set resize to one of kResizeNone, kResizeWidth, kResizeHeight, kResizeFit, kResizeFill, kResizeDistort.
    Set to_type to one of kCustom, kToScale, or kToBox.
    Supply the flag for center, defaults to True.
    Supply the flag for flip, defaults to False.
    Supply the flag for flop, defaults to False.
    Supply the flag for turn, defaults to False.
    Supply format in a tuple of (width, height, pixel aspect, name).
    Supply scale as a single floating point number.
    Supply box in a tuple of (width, height, pixel aspect).
    Note that this will always set "black outside"."""

    Node.__init__(self, "Reformat", resize=resize, black_outside=black_outside)

    self.setKnob("type", to_type)
    self.setKnob("center", center)
    self.setKnob("flip", flip)
    self.setKnob("flop", flop)
    self.setKnob("turn", turn)
    if filter:
      self.setKnob("filter", filter)
    self.setKnob("pbb", pbb)
    if to_type == self.kToFormat:
      if format is None or not str(format):
        raise ValueError("to_type is set to kToFormat but format is not a format string (it is %s)." % (str(type(format)),))
      self.setKnob("format", format)
    elif to_type == self.kToScale:
      if scale is None or not float(scale) > 0:
        raise ValueError("to_type is set to kToScale but scale is not a positive floating point number.")
      self.setKnob("scale", scale)
    elif to_type == self.kToBox:
      if box is None or len(box) != 3:
        raise ValueError("to_type is set to kToBox but box is not a tuple of (width, height, pixel aspect).")
      self.setKnob("box_width", box[0])
      self.setKnob("box_height", box[1])
      self.setKnob("box_pixel_aspect", box[2])
      self.setKnob("box_fixed", "true")
    elif to_type == self.kDisabled:
      pass
    else:
      raise ValueError("unknown reformat to_type '%s'" % (to_type,))



class MetadataNode (Node):
  """ Class which corresponds to the Nuke ModifyMetaData node. """

  # Table of characters which need to be escaped when generating the text for the metadata knob
  kCharacterEscapeTable = (
    ("\\", "\\\\"),
    ("{", "\\{"),
    ("}", "\\}")
  )

  def __init__(self, metadatavalues=None, inputNode=None, inputs=1):
    Node.__init__(self, "ModifyMetaData", inputNode0=inputNode, inputs=inputs)
    self._metadataValues = {}
    if metadatavalues is not None:
      self.addMetadata(metadatavalues)

  def escape(self, value):
    """ Make sure metadata strings are properly escaped, following the kCharacterEscapeTable. """
    value = str(value) # Input might not be a str, convert it
    for before, after in MetadataNode.kCharacterEscapeTable:
      value = value.replace(before, after)
    return value
      
  def addMetadata ( self, metadatavalues ):
    """ Add keys/values to the metadata.  metadatavalues should either be a dict or a list of tuples with (key, value). """
    # Add the keys to the metadata dict
    self._metadataValues.update(metadatavalues)
    # Generate the text for the metadata knob
    self.setKnob("metadata", "{%s}" % " ".join([ "{set %s \"%s\"}" % (self.escape(key), self.escape(value)) for key,value in self._metadataValues.items()]))

  def addMetadataFromTags(self, tags):
    """ Add metadata from a list of tags. """
    unwantedKeys=["tag.applieswhole","tag.guid","tag.label","tag.note"]
    self.addMetadata([ ('"hiero/tags/' + tag.name() + '"', tag.name()) for tag in tags])
    self.addMetadata([ ('"hiero/tags/' + tag.name() + '/note"', tag.note()) for tag in tags])
    for tag in tags:
      name = tag.name()
      meta = tag.metadata()
      self.addMetadata([ ('"hiero/tags/' + name + '/'+key[4:]+'"', meta.value(key)) for key in list(tag.metadata().keys()) if key not in unwantedKeys])



class RootNode(Node):

  kTimelineWriteNodeKnobName = "timeline_write_node"

  def __init__(self, first_frame, last_frame, fps=None, showAnnotations=False):
    Node.__init__(self, "Root", first_frame=first_frame, last_frame=last_frame, lock_range='true')

    # change _knobValues to be a OrderedDict so the order in which knob values are added can remain the same.
    # workingSpaceLUT knob value needs to be written after colorManagement, OCIO_config and customOCIOConfigPath
    self._knobValues = collections.OrderedDict(self._knobValues)

    if fps is not None:
      self.setKnob("fps", fps)
  
    # When Nuke goes to read an image, it checks if the already loaded plugins can read it
    # ffmpeg and mov reader can read mp4 and m4v files, but only if they're already loaded
    # If they're not loaded, then Nuke checks the file extension and tries to load a plugin with that
    # name (i.e. mp4Reader). But Nuke doesn't have one of those.
    # So we force it to load.
    loadMovStuffScript = '''if nuke.env['LINUX']:
  nuke.tcl('load ffmpegReader')
  nuke.tcl('load ffmpegWriter')
else:
  nuke.tcl('load movReader')
  nuke.tcl('load movWriter')'''
    self.setKnob("onScriptLoad", loadMovStuffScript)

    # Add a tab inside which all the user knobs we add will be placed
    self.addTabKnob("studio", text="Studio")

    # Add a knob for controlling the visibility of annotations
    # This probably isn't needed any more, and the options have been removed from the NukeShotExporterUI.  Hiding in the script.
    self.addCheckboxKnob("annotations_show",
                          text="Show Annotations",
                          tooltip="Control whether annotations are visible.",
                          value=showAnnotations,
                          visible=False)

    self.addInputTextKnob(RootNode.kTimelineWriteNodeKnobName,
                            text="Timeline Write Node",
                            tooltip="The name of the Write node which should be used when showing the comp on the timeline.")


  def _setLUTKnob(self, key, lut, converRawToLinear):
    # don't filter out or error on non nuke built-in luts; doing so would make it so that
    # clients couldn't have their own custom luts in Hiero and Nuke.

    if converRawToLinear and lut in ("raw", "None"):
      lut = "linear"

    # If no lut is set, skip this knob
    if lut != None:
      self.setKnob(key, lut)

  def addProjectSettings(self, projectSettings):
    """ Add knobs related to the color management options to the node. """

    converRawToLinear = False

    # Get the OCIO config path
    ocioConfig = projectSettings["ocioConfigPath"]
    # Check the OCIO export option
    if projectSettings['lutUseOCIOForExport']:

      # Enable the custom OCIO config in the root node
      self.setKnob("colorManagement", "OCIO")

      # Has a ocio config been set in the project settings?
      if not projectSettings['useOCIOEnvironmentOverride']:
        ocioConfigName = projectSettings['ocioConfigName']
        if not ocioConfig:
          self.setKnob("OCIO_config", "nuke-default")
        elif ocioConfigName:
          self.setKnob("OCIO_config", ocioConfigName)
        else:
          self.setKnob("OCIO_config", "custom")
          self.setKnob("customOCIOConfigPath", ocioConfig)
    else:
      self.setKnob("colorManagement", "Nuke")
      # nuke builtin luts don't have raw, only linear
      converRawToLinear = True

    self._setLUTKnob("workingSpaceLUT"  , projectSettings['lutSettingWorkingSpace'], converRawToLinear)
    self._setLUTKnob("monitorLut"       , projectSettings['lutSettingViewer'], converRawToLinear)
    self._setLUTKnob("int8Lut"          , projectSettings['lutSetting8Bit'], converRawToLinear)
    self._setLUTKnob("int16Lut"         , projectSettings['lutSetting16Bit'], converRawToLinear)
    self._setLUTKnob("logLut"           , projectSettings['lutSettingLog'], converRawToLinear)
    self._setLUTKnob("floatLut"         , projectSettings['lutSettingFloat'], converRawToLinear)

  def setViewsConfiguration(self, viewsColors, heroView=None, showColors=None):
    """ Set the view related knobs on the Root node """
    viewsString = '"' + '\n'.join(('{} {}'.format(v, c.name()) for v, c in viewsColors)) + '"'
    self.setKnob('views',  viewsString)
    if heroView:
      self.setKnob('hero_view', heroView)
    if showColors is not None:
      self.setKnob('views_colours', showColors)


class FrameRangeNode(Node):
  """ FrameRange node class. """
  
  def __init__(self, first_frame, last_frame):
    """ Construct the node with first and last frame. """
    Node.__init__(self, "FrameRange", first_frame=first_frame, last_frame=last_frame)
  
  def getNodeSize(self):
    """ Get the size of the node.  This is an estimate, since in Nuke the size can be affected by
      the font size (and possibly other factors), but it works in most cases for layout of scripts. """
    return 80, 32


class TimeClipNode(Node):
  """ TimeClip node class. """
  
  def __init__(self, ifirst, ilast, origFirst, origLast, startTime ):
    Node.__init__(self,
                  "TimeClip",
                  first=ifirst,
                  last = ilast,
                  frame=startTime,
                  origfirst=origFirst,
                  origlast=origLast,
                  origset=1,
                  frame_mode="start at",
                  mask_metadata="true")
  
  def getNodeSize(self):
    """ Get the size of the node.  This is an estimate, since in Nuke the size can be affected by
      the font size (and possibly other factors), but it works in most cases for layout of scripts. """
    return 80, 32




class ConstantNode(Node):
  """ Constant node class. """

  def __init__(self, first, last, channels="none", **knobs):
    """ Construct the node with first and last frames. """
    Node.__init__(self, "Constant", first=first, last=last, channels=channels, **knobs)


  def getNodeSize(self):
    """ Get the size of the node.  This is an estimate, since in Nuke the size can be affected by
        the font size (and possibly other factors), but it works in most cases for layout of scripts. """
    return 80, 78

class DotNode(Node):
  """ Dot node class. """

  def __init__(self, **knobs):
    """ Construct the node. """
    Node.__init__(self, "Dot", None, **knobs)

  def align(self, inputNode, outputNode):
    """ align the Node vertically below its input and horizontally with its output. """
    inputNodeX, inputNodeY = inputNode.getPosition()
    inputNodeW, inputNodeH = inputNode.getNodeSize()

    outputNodeX, outputNodeY = outputNode.getPosition()
    outputNodeW, outputNodeH = outputNode.getNodeSize()

    dotNodeW, dotNodeH = self.getNodeSize()

    xPos = inputNodeX + (inputNodeW / 2) - (dotNodeW / 2)
    yPos = outputNodeY + (outputNodeH / 2) - (dotNodeH / 2)

    self.setPosition(xPos, yPos)

  def getNodeSize(self):
    """ Get the size of the node.  This is an estimate, since in Nuke the size can be affected by
        the font size (and possibly other factors), but it works in most cases for layout of scripts. """
    return 12, 12


class BackdropNode(Node):
  """ BackdropNode class. """

  def __init__(self, xpos, ypos, width, height):
    """ Construct the backdrop with x, y, width, height. """
    Node.__init__(self, "BackdropNode", xpos=xpos, ypos=ypos, bdwidth=width, bdheight=height)


  def setLabel(self, text):
    """ Set the node label.  Adds the center tag to it. """
    self.setKnob("label", "<center>%s" % text)


  def setColor(self, color):
    """ Set the backdrop color. """
    self.setKnob("tile_color", color)


  def setZOrder(self, zorder):
    """ Set the z ordering for the backdrop. """
    self.setKnob("z_order", zorder)


  def setLabelFontSize(self, size):
    """ Set the font size of the label. """
    self.setKnob("note_font_size", size)


  def getNodeSize(self):
    """ Get the backdrop size. """
    return self.knob("bdwidth"), self.knob("bdheight")


class DissolveNode(Node):
  """ Dissolve node. """

  def __init__(self):
    # Initialize with default knob values
    Node.__init__(self, "Dissolve", inputs=2, mergerange=True)


  def setWhichKeys(self, *keys):
    """ Set the keys for the which knob as a set of tuples with (frame, value) """
    which = "{{curve L " + " ".join( [ "x%s %s" % (k, v) for k, v in keys ] ) + "}}"
    self.setKnob("which", which)
    
  def getNodeSize(self):
    """ Get the size of the node.  This is an estimate, since in Nuke the size can be affected by
        the font size (and possibly other factors), but it works in most cases for layout of scripts. """
    return 80, 32
