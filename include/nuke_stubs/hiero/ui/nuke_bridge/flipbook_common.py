import nuke_internal as nuke
import re

"""
Common functions used by the Nuke and Player flipbook implementations
"""

def getColorspaceFromNode( node ):
  """ If node is Read or Write it returns the colorspace known value,
  for the remaining nodes 'linear' will be returned"""

  inputColourspace = "linear"   # Consider changing this to return an empty string if non-nuke-default config being used.

  # Default to whatever the working space is for the current config, this will be fine for all configs,
  # inlcuding nuke-default.
  rootNode = nuke.root()
  if rootNode:
    workingSpaceKnob = rootNode.knob("workingSpaceLUT")
    if workingSpaceKnob:
      inputColourspace = workingSpaceKnob.value()

  # Check if we have a different than linear input
  if node.Class() == "Read" or node.Class() == "Write":
    lut = node.knob("colorspace").value()
    # Might be in the format of "default (foo)", if so, get at "foo".
    if lut.startswith("default ("):
      lut = lut[9:-1]
    inputColourspace = lut

  return inputColourspace


def getIsUsingNukeColorspaces(rootNode):
  """Helper function that returns True if the the specified root node is using the original Nuke color management
  and False otherwise, i.e. when OCIO color management is being used."""

  usingNukeColorspaces = False
  if rootNode:
    colorManagementKnob = rootNode.knob("colorManagement")
    if colorManagementKnob:
      usingNukeColorspaces = (colorManagementKnob.value() == "Nuke")  # Note: must use value() rather than getValue()

  return usingNukeColorspaces


# Regex for the format used by Nuke viewer LUT strings (which is different from
# the format used by the sequence/flipbook viewer
kNukeViewerLUTFormat = '(.*) \((.*)\)'


def mapViewerLUTString( lut ):
  """ Map a viewer LUT string into the form expected by the flipbook viewer """
  res = re.match( kNukeViewerLUTFormat , lut)
  if res is not None:
    return "%s/%s" % ( res.group(2) , res.group(1) )
  else:
    return lut


def getRawViewerLUT():
  """ Helper function to return a 'raw' viewer LUT string compatible with the
  current color management mode, and current OCIO config if OCIO color management
  is being used. In the case of OCIO, other than when using the nuke-default
  config, this does a case-insensitive search through the available combinations
  of displays and views, looking for the first view whose name is 'raw' (using a
  case insensitive check). """

  rawViewerLUT = ""
  rootNode = nuke.root()
  if getIsUsingNukeColorspaces(rootNode):
    # We're using the original Nuke color management so we just need to return 'None'.
    rawViewerLUT = "None"
  else:
    # We're using OCIO color management.
    # First determine whether we're using the nuke-default config, as (unlike all others I've seen)
    # that does not contain a view called 'Raw' but instead has one called 'None' (based on the equivalent
    # entry in the non-OCIO color management).
    usingNukeDefaultConfig = False
    if rootNode:
      ocioConfigKnob = rootNode.knob("OCIO_config")
      if ocioConfigKnob:
        usingNukeDefaultConfig = (ocioConfigKnob.value() == "nuke-default")

    if usingNukeDefaultConfig:
      # Special case for nuke-default config.
      # The flipbook (i.e. timeline) viewer expects the string to be in the form "<display name>/<view name>".
      rawViewerLUT = "default/None"
    else:
      # Look through the viewer transforms available for the current config, which Nuke has stored
      # in the form "<view name> (<display name>)".
      availableLUTs = nuke.ViewerProcess.registeredNames()
      for availableLUT in availableLUTs:
        matchResult = re.match( kNukeViewerLUTFormat , availableLUT)
        if matchResult is not None:
          viewName = matchResult.group(1)
          displayName = matchResult.group(2)
          # We'll use the transform for the first viewer name we find that is called 'raw' (case-insensitive).
          # The flipbook (i.e. timeline) viewer expects the string to be in the form "<display name>/<view name>".
          if viewName.lower() == "raw":
            rawViewerLUT = "%s/%s" % (displayName, viewName)
            break
          elif not rawViewerLUT:
            # Default to the first available transform in case we don't find one called 'raw'.
            rawViewerLUT = "%s/%s" % (displayName, viewName)

  return rawViewerLUT


def getOCIOConfigPath():
  """ Returns the OCIO config filepath used in the Nuke project.
      Returns an empty string if using Nuke Root LUTs"""
  OCIOConfigPath = ''
  root = nuke.root()
  useDefaultLUTs = root['defaultViewerLUT'].value() == 'Nuke Root LUTs'
  if not useDefaultLUTs:
    useCustomOCIO = root['OCIO_config'].value() is 'custom'
    if useCustomOCIO:
      OCIOConfigPath = root['customOCIOConfigPath'].value()
    else:
      OCIOConfigPath = root['OCIOConfigPath'].value()
  return OCIOConfigPath


# Capabilities supported by the internal flipbooks
kNukeFlipbookCapabilities = {
  'roi': False, # TODO Surely we could support this?
  'canPreLaunch': False,
  'arbitraryChannels': True,
  # Needed for the code to know more than one view is supported, the actual number doesn't matter as long as it's > 1
  'maximumViews' : 2,
  # The internal flipbook supports all the Read file types that the node graph does
  'fileTypes' : ["*"]
}
