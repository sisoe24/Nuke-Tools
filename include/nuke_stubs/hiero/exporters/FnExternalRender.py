# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import hiero.core
import hiero.core.nuke as nuke
import hiero.core.log as log
import hiero.core.FnExporterBase as FnExporterBase
import hiero.core.FnNukeHelpers as FnNukeHelpers
from hiero.core.FnFloatRange import Default, CustomList
from . import FnShotExporter
import os.path
import sys
import ocionuke

kPerShot = "Shot"
kPerTrack = "Track"
kPerSequence = "Sequence"
kUnconnected = "Unconnected"
kDisabled = "None"

# Generic external render content.
class ExternalRenderTask(FnShotExporter.ShotTask):
  """ExternalRenderTask doesn't do anything, it's just a marker to go into the template
  so that other tasks can find the location of external renders."""
  def __init__(self, initDict ):
    """Initialize"""
    FnShotExporter.ShotTask.__init__(self, initDict)

  def taskStep(self):
    return FnShotExporter.ShotTask.taskStep(self)
  
class ExternalRenderPreset(hiero.core.TaskPresetBase):
  def __init__(self, name, properties):
    """Initialise presets to default values"""
    hiero.core.TaskPresetBase.__init__(self, ExternalRenderTask, name)
    
    self.properties().update(properties)

  def supportedItems(self):
    return hiero.core.TaskPresetBase.kTrackItem
    
hiero.core.taskRegistry.registerTask(ExternalRenderPreset, ExternalRenderTask)


def createAdditionalNodes(entrypoint, additionalNodeData, item):
  """Return list of nodes to be added to the script at specified entrypoint based on item tags"""
  """@param entrypoint: kPerShot, kPerTrack, kPerSequence, kUnconnected, kDisabled - entry point within nuke script"""
  """@param item: item being exported"""
  """@return [nuke.UserDefinedNode, ]"""
  
  itemtags = FnExporterBase.tagsFromSelection([item], includeParents=True)
  
  nodes = []
  for location, tags, script in additionalNodeData:
    if not script:
      continue
    if location == entrypoint:
      if not tags or [tag.name() for tag, parentType in itemtags if tag.name() in tags]:
        nodes.append(nuke.UserDefinedNode(script))
  return nodes
  
def _mapDefaultColourTransform (preset, projectsettings):
  properties = preset.properties()

  # Get File Type
  file_type_key = "file_type"
  file_type = properties[file_type_key] if file_type_key in properties else None

  # Pull default datatype from codec settings
  data_type_key = "datatype"        
  codec_settings = preset._codecSettings[file_type]["properties"]
  data_type_default = None
  data_type_default_list = codec_settings[data_type_key] if data_type_key in codec_settings else None
  
  if hasattr(data_type_default_list, '__iter__'):
    data_type_default = data_type_default_list[0]
    for data_type in data_type_default_list:
      if isinstance(data_type, Default):
        data_type_default = data_type.value()
        break

  # Get datatype from properties
  data_type = properties[file_type][data_type_key] if file_type in properties and data_type_key in properties[file_type] else data_type_default

  int8 = '8Bit'
  int16 = '16Bit'
  float = 'Float'
  log = 'Log'

  mapping_table = { 'cin' : log,
                    'dpx' : {"8 bit" : int8, "10 bit" : log , "12 bit" : int16, "16 bit" : int16},
                    'exr' : float,
                    'ffmpeg' : int8,
                    'hdr' : float,
                    'jpeg' : int8,
                    'mov' : int8,
                    'pic' : int8,
                    'png' : int8,
                    'sgi' : { "8 bit" : int8, "16 bit" : int16 },
                    'targa' : int8,
                    'tiff' : { "8 bit" : int8, "16 bit" : int16, "32 bit float" : float } }

  if file_type in mapping_table:

    lut_key = None
    if isinstance(mapping_table[file_type], dict):
      # is datatype dictionary
      if data_type in mapping_table[file_type]:
        lut_key = mapping_table[file_type][data_type]
    else:
      lut_key = mapping_table[file_type]
    
    lut = projectsettings['lutSetting' + lut_key]
    if lut is None:
      raise RuntimeError("OCIO : Output colourspace set to Default but project Colour Management settings for < %s > is not set." % lut_key)
    
    return lut
    
  return None


def getRoleFromPropertyWithRole(lutValue):
  """Get just the role name from a string containing the colorspace +
  the role in parentheses."""
  if lutValue.endswith(")"):
    return lutValue[ : lutValue.find('(') - 1]

  assert False, ("This function should not be used unless the colorspace contains a role")

def getColorspaceFromPropertyWithRole(lutValue):
  """Get just the colorspace name from a string containing the colorspace +
  the role in parentheses."""
  if lutValue.endswith(")"):
    return lutValue[lutValue.find('(')+1 : -1]

  assert False, ("This function should not be used unless the colorspace contains a role")

def getColorspaceAndRoleSplit(lutValue):
  """Returns the colorspace and role if the string contains both, otherwise returns
  the provided lutValue as the colorspace and None as the role"""
  if lutValue.endswith(")"):
    potentialRole = getRoleFromPropertyWithRole(lutValue)
    if ocionuke.config.getOCIOConfig().hasRole(potentialRole):
      colorspace = getColorspaceFromPropertyWithRole(lutValue)
      return colorspace, potentialRole

  return lutValue, None

def isColorspaceValid(project, colorspace, role):
  # If a non-default colour transform is set, validate that it actually exists
  # in the current project configuration.  This check should probably be done
  # earlier, but there's no appropriate place to do it.
  if colorspace == "default":
    return True

  luts = hiero.core.LUTs(project)
  if role:
    return role in luts

  return colorspace in luts

def createWriteNode(ctx, path, preset, nodeName=None, inputNode=None, framerate=None, project=None):
  """Return a Nuke Write node based on a path and a preset."""
  properties = preset.properties()

  fileType = properties["file_type"]
  presetCodecProperties = None
  
  writeNode = nuke.WriteNode(path, inputNode)
  if fileType in properties:
    writeNode.setKnob("file_type", fileType)

    if presetCodecProperties is None:
      presetCodecProperties = preset.codecProperties().copy()
    
    for key in presetCodecProperties.keys():
      # If the key is not a string, then we assume it is
      # a tuple containing both the label and the actual key name
      # we are after.
      if not isinstance(key, str):
        label, key = key
      if key in properties[fileType]:
        value = properties[fileType][key]
        if value is None:
          continue
        
        writeNode.setKnob(key, str(value))

  colourTransform = properties.get("colourspace", None)
  if colourTransform:
    colorspace, role = getColorspaceAndRoleSplit(colourTransform)
    isValidTransform = isColorspaceValid(project, colorspace, role)
    if not isValidTransform:
      raise RuntimeError("Unable to create Write node with invalid color space: %s" % colourTransform)
    
    projectsettings = project.extractSettings()
    colourTransform = FnNukeHelpers.nukeColourTransformNameFromHiero(colorspace, projectsettings)

  projectsettings = project.extractSettings()
  if projectsettings["lutUseOCIOForExport"] is True:

    # If the colour transform hasnt been set or if set to default,
    # we need to mimic the default colourspace of nukes write node
    # Using the colour
    if colourTransform in (None, "default"):
      colourTransform = _mapDefaultColourTransform(preset, projectsettings)

    def isLog(colourspace):
      for possibleLog in ("lg", "log"):
        if possibleLog in colourspace:
          return True
      return False

    if fileType == "dpx":
      colourTransformGroup = hiero.core.LUTGroup(project, colourTransform)
      if isLog(colourTransform) or isLog(colourTransformGroup):
        writeNode.setKnob("transfer", "log")

  if colourTransform is not None:
    writeNode.setKnob("colorspace", colourTransform)

  # Set the views knob. If set to all, this is the default for Write nodes,
  #so no need to write the knob in that case
  views = properties['views']
  if views != hiero.core.RenderTaskPreset.AllViews():
    writeNode.setKnob('views', '{' + ' '.join(views) + '}')
  
  # If channels property set, add knob to write node.
  if "channels" in properties:
    writeNode.setKnob("channels", properties["channels"])
      
  # Set quicktime flag to write timecode track. Ignores if no timecode present.
  if fileType is "mov":
    # have to special case framerate
    if framerate != None:
      
      # Nuke is special and inconsistent with how the quicktime (windows/mac) writer handles fps
      # We have to also handle the advanced settings, which can include the framerate in them
      writeNode.setKnob("fps", framerate)

  # If a Node Name has been specified add to node
  if nodeName:
    writeNode.setKnob("name", nodeName)

  # Set the create_directories knob
  if "create_directories" in properties:
    writeNode.setKnob("create_directories", properties["create_directories"])
      
  log.debug( "NukeRenderTask generated WriteNode:" )
  log.debug( str(writeNode) )
  return writeNode

# Nuke Render
class NukeRenderTask(ExternalRenderTask):
  """NukeRenderTask holds settings for a Nuke Write node so that shot exports can create
  the node set up to write to the requested location."""
  def __init__(self, initDict ):
    """Initialize"""
    ExternalRenderTask.__init__(self, initDict )

    # We have some more information for the resolver, add it to the table.
    #self._resolveTable["{ext}"] = preset.extension()

  def taskStep(self):
    return ExternalRenderTask.taskStep(self)

  def nukeWriteNode(self, framerate=None, project=None):
    """Return a Nuke Write node for this tasks's export path."""
    nodeName = None
    presetProperties = self._preset.properties()
    if "writeNodeName" in presetProperties and presetProperties["writeNodeName"]:
      nodeName = self.resolvePath(presetProperties["writeNodeName"])
    return createWriteNode(self, self.resolvedExportPath(), self._preset, nodeName, framerate=framerate, project=project)

  def viewsFromPreset(self):
    """ Get the views configured on the preset. """
    return self._preset.properties()["views"]

  def viewsFromSource(self):
    """ Get the views available from the source sequence/clip/trackitem. By default
    returns all the views in the project.
    """
    return self._project.views()

  def views(self):
    presetViews = self.viewsFromPreset()
    sourceViews = self.viewsFromSource()
    if presetViews == hiero.core.RenderTaskPreset.AllViews():
      views = self.viewsFromSource()
    else:
      views = presetViews
    return views

  def validate(self):
    super(NukeRenderTask, self).validate()

    # Check that the views selected to render are valid for the task input
    presetViews = self.viewsFromPreset()
    if not presetViews:
      raise RuntimeError('Render task has no views selected')
    sourceViews = self.viewsFromSource()
    if not sourceViews:
      raise RuntimeError('Render task has no views from source item')
    if presetViews != hiero.core.RenderTaskPreset.AllViews():
      for view in presetViews:
        if not view in sourceViews:
          raise RuntimeError('Render task has invalid view "{}"'.format(view))
  
  def addBurninNodes(self, script=None):
    """If Burnin enabled in preset, add NukeRenderTask.burninNodeData to the 
    script and modify knob values according to preset data"""
    
    burninNode = None
    
    # Burnin enabled?
    if self._preset.properties()["burninDataEnabled"]:
      burninNodeData = str(NukeRenderTask.burninNodeData)
      
      def getDefault(value):
        if isinstance(value, CustomList):
          return value.default()
        elif hasattr(value, '__iter__'):
          for v in value:
            if isinstance(v, Default):
              return v
        return value
        
      defaults = dict ( (datadict['knobName'], getDefault(datadict['value'])) for datadict in NukeRenderTask.burninPropertyData )
      
      # For each knob/value in the preset
      for key, value in self._preset.properties()["burninData"].items():
        # replace any matches of <knobname>_value with the knob value from the preset
        if value is None:
          value = defaults[key]
        
        if isinstance(value, str):
          for token, metadatakey in NukeRenderTask.burninKeys:
            value = value.replace(token, metadatakey)
          
        burninNodeData = burninNodeData.replace("%s_value" % key, "\"%s\"" % str(value))
      
      burninNode = nuke.UserDefinedNode(burninNodeData)
      if script is not None:
        script.addNode(burninNode)

    return burninNode


class NukeRenderPreset(hiero.core.RenderTaskPreset):
  def __init__(self, name, properties):
    """Initialise presets to default values"""
    hiero.core.RenderTaskPreset.__init__(self, NukeRenderTask, name, properties)
    
    if "writeNodeName" not in self.properties():
      self.properties()["writeNodeName"] = "Write_{ext}"
    
    self.properties()["burninDataEnabled"] = False
    self.properties()["burninData"] = dict((datadict["knobName"], None) for datadict in NukeRenderTask.burninPropertyData)

    self._properties["create_directories"] = True
    
    self._properties.update(properties)
    
  def supportedItems(self):
    return hiero.core.TaskPresetBase.kAllItems
    

NukeRenderTask.burninKeys = (("{sequence}", "[metadata hiero/sequence]"), ("{clip}", "[metadata hiero/clip]"), ("{shot}", "[metadata hiero/shot]"), ("{track}", "[metadata hiero/track]"), ("{project}", "[metadata hiero/project]"), ("{timecode}", "[metadata input/timecode]"))    
# Load gizmo from file 'BurnInGroup.nk'. add knobName_value to .nk file where properties should be injected.
NukeRenderTask.burninNodeData = open(os.path.join(os.path.dirname(__file__), "BurnInGroup.nk")).read()
# Set properties which will be reflected into the edit burnin UI
NukeRenderTask.burninPropertyData = (  
                          {'label':"Text Size", 'knobName':"burnIn_textSize", 'value' : 43.5 },
                          #burnIn_colour {1 1 1}
                          {'label':"Padding", 'knobName':"burnIn_padding", 'value' : 40},
                          {'label':"Font", 'knobName':"burnIn_font", 'value' : ""},
                          {'label':"Top Left", 'knobName':"burnIn_topLeft", 'value' : CustomList( *[token for token, key in NukeRenderTask.burninKeys], default="{clip}")},
                          {'label':"Top Middle", 'knobName':"burnIn_topMiddle", 'value' : CustomList( *[token for token, key in NukeRenderTask.burninKeys], default="{sequence}")},
                          {'label':"Top Right", 'knobName':"burnIn_topRight", 'value' : CustomList( *[token for token, key in NukeRenderTask.burninKeys], default="{shot}")},
                          {'label':"Bottom Left", 'knobName':"burnIn_bottomLeft", 'value' : CustomList(*[token for token, key in NukeRenderTask.burninKeys], default="{track}")},
                          {'label':"Bottom Middle", 'knobName':"burnIn_bottomMiddle", 'value' : CustomList(*[token for token, key in NukeRenderTask.burninKeys], default="{project}")},
                          {'label':"Bottom Right", 'knobName':"burnIn_bottomRight", 'value' : CustomList(*[token for token, key in NukeRenderTask.burninKeys], default="{timecode}")} )
 


hiero.core.taskRegistry.registerTask(NukeRenderPreset, NukeRenderTask)
