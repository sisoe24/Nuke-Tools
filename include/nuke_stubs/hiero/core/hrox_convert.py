import sys
import os
from collections import OrderedDict
from PySide2.QtCore import QFile, QTextStream
from PySide2.QtXml import QDomDocument, QDomElement
import colorsys
import math
import itertools
import re

"""
Script for converting hrox files from older versions.
"""

# When writing, there doesn't seem to be a way to get the XML lib to write the
# DOCTYPE or processing instructions. These are written to the file before
# writing the document
_kDocumentHeader = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE hieroXML>\n'

# hrox project versions to convert between, stored as an attribute on the root 'hieroXML' element.
# Note this is not related to the application version number
_kFromProjectVersions = ('8', '9', '10')
_kToProjectVersion = '11'

# Current Nuke version, inserted into the hrox. Should be updated with each release
_kCurrentVersionString = '11.1v1'

# List of extensions for all video media formats which Nuke must read at frame 1 or later (not frame zero)
# TODO This list is duplicated in hiero.core.__init__.py and the C++ code. Should be cleaned up
_kNonZeroStartFrameMovieFileExtensions = (
".mov", ".m4v", ".mp4", ".m4a", ".m4p", ".m4b", ".m4r", ".mpg", ".mpeg", ".avi", ".mxf")

# Lookup tables for the R3D enumerated parameters. These are stored as ints in the
# hrox, and the values do not necessarily correspond to the int values used in the
# r3dReader. Convert them to the string representation.
_kR3DDecodeModes = {
  '0' : 'FullHigh',
  '1' : 'HalfHigh',
  '2' : 'HalfGood',
  '3' : 'QuarterGood',
  '4' : 'EighthGood',
  '5' : 'SixteenthGood'
}

_kR3DColorSpaces = {
  '12' : 'DRAGONcolor2',
  '11' : 'REDcolor4',
  '15' : 'REDWideGamutRGB',
  '13' : 'Rec2020',
  '1' : 'Rec709',
  '4' : 'SRGB',
  '5' : 'Adobe1998',
  '0' : 'CameraRGB',
  '2' : 'REDspace',
  '3' : 'REDcolor',
  '6' : 'REDcolor2',
  '8' : 'REDcolor4',
  '9' : 'DRAGONcolor',
}

_kR3DGammaSpaces = {
  '12' : 'REDgamma4',
  '9' : 'REDlogFilm',
  '0' : 'Half Float Linear',
  '1' : 'Rec709',
  '8' : 'SRGB',
  '14' : 'HDR2084',
  '15' : 'BT1886',
  '16' : 'Log3G12',
  '18' : 'Log3G10',
  '4' : 'PDlog685',
  '5' : 'PDlog985',
  '6' : 'CustomPDlog',
  '2': 'REDspace',
  '3' : 'REDlog',
  '7': 'REDgamma',
  '10': 'REDgamma2',
  '11': 'REDgamma3',
}


_kArriColourSpaces = {
  '5' : "LogC - Wide Gamut",
  '1' : "LogC - Camera Native",
  '4' : "LogC - Film",
  '0' : "Video - Rec 709",
  '2' : "Video - P3-DCI",
  '3' : "SceneLin. - ACES",
  '6' : "LogC - Monochrome",
  '7' : "Video - Monochrome",
  '8' : "SceneLin. - Wide Gamut",
  '9' : "SceneLin. - Cam. Nat.",
  '10' : "Video - Rec 2020",
  '11' : "Video - P3-D60",
  '12' : "Video - P3-D65"
}

_kArriResolutions = [
  "Clean Open Gate",
  "2880 native",
  "2K",
  "2K DCP",
  "HD",
  "SD",
  "4K",
  "4K DCP",
  "UHD-1",
  "2868 cropped",
  "2578 4:3 cropped ARRIRAW",
  "Alexa65 4.3k",
  "Alexa65 5k",
  "Alexa65 6k",
  "ALEXA SXT ARRIRAW 3.2K",
  "ALEXA OpenGate, full sensor",
  "4:3 cropped",
  "XA SXT ARRIRAW 3.2K framegrabs",
  "ALEXA Mini 8:9",
]

_kArriAspectRatios = [
  "1.33",
  "1.55",
  "1.78",
  "1.85",
  "2.39",
  "1.19",
  "1.5",
  "2.12"
]

_kArriLensSqueeze = [
  "1.0",
  "1.3",
  "2.0",
  "1.25",
]

_kArriProxyModes = [
  "Off",
  "Full (1:1)",
  "Half (1:2)"
]

_kArriDebayeringMode = [
  "ADA-1 HW",
  "ADA-2 SW",
  "ADA-3 SW",
  "ADA-3 HW",
  "ADA-5 SW",
  "ADA-5 HW",
]

class R3DLggParamConverter(object):
  """ Functor for converting the R3D lift-gamma-gain parameters from the way
  they're stored in old hrox files to the values needed for the knobs.
  The maths here is taken directly from the C++ code which has to do this
  conversion for passing to the R3D SDK.
  """

  _kHueAngleOffset = 250.0

  def __init__(self, isLift):
    self._isLift = isLift

  @staticmethod
  def _rgbToHsv(r, g, b):
    m = min(r, g, b)
    mx = max(r, g, b)
    h, s, v = colorsys.rgb_to_hsv(r - m, g - m, b - m)
    y = (r + g + b) / 3.0
    s = mx - m
    v = y
    return h, s, v

  @staticmethod
  def _rgbToRedXY(r, g, b):
    h, s, v = R3DLggParamConverter._rgbToHsv(r, g, b)
    radius = s * 0.5
    theta = 2.0 * math.pi * (3.0 * h + 1.0) / 3.0
    bias = v
    x = radius * math.cos(theta)
    y = radius * math.sin(theta)
    return x, y, bias

  @staticmethod
  def _xyToRgb(x, y, bias, isLift):
    radius = math.sqrt(math.pow(x,2) + math.pow(y,2))
    theta = math.atan2(y, x)
    hsv_x = (R3DLggParamConverter._kHueAngleOffset + 360.0 * (theta / (2 * math.pi))) / 360.0
    hsv_y = 2.0 * radius
    hsv_z = 1.0
    r, g, b = colorsys.hsv_to_rgb(hsv_x, hsv_y, hsv_z)
    mean = (r + g + b) / 3.0
    diff = 1.0 - mean
    r += diff
    g += diff
    b += diff

    if isLift:
      r += (bias - 1.0)
      g += (bias - 1.0)
      b += (bias - 1.0)
    else:
      r *= (bias + 1.0)
      g *= (bias + 1.0)
      b *= (bias + 1.0)
    return r, g, b

  @staticmethod
  def _mapLggParam(r, g, b, isLift):
    x, y, bias = R3DLggParamConverter._rgbToRedXY(r, g, b)
    outR, outG, outB = R3DLggParamConverter._xyToRgb(x, y, bias, isLift)
    return outR, outG, outB

  def __call__(self, value):
    # Split the RGB components, which are in a comma separated string
    r, g, b = [ float(x) for x in value.split(',') ]

    # Map the values and return a string in nk script form
    outR, outG, outB = R3DLggParamConverter._mapLggParam(r, g, b, self._isLift)
    return '{%f %f %f}' % (outR, outG, outB)


def _isValidElem(elem):
  """ Helper to check for valid QDomElement instances. Qt methods will return null 
  QDomElement objects which don't evaluate false in Python so need to check this. 
  """
  return isinstance(elem, QDomElement) and not elem.isNull()


def _findFirstInElem(elem, path):
  """ Find the first child element matching path. """
  for name in path.split('/'):
    childElem = elem.firstChildElement(name)
    if not _isValidElem(childElem):
      elem = None
      break
    else:
      elem = childElem
  return elem


def _findAllInElem(elem, path):
  """ Find all elements matching path. """
  # If the path contains / find the first element matching the path apart from the 
  # end
  lastSlash = path.rfind('/')
  if lastSlash != -1:
    elem = _findFirstInElem(elem, path[:lastSlash])
    name = path[lastSlash+1:]
  else:
    name = path

  # Find all the children matching the end of the path
  children = []
  if _isValidElem(elem):
    for child in _iterElem(elem, False, name):
      children.append(child)
  return children


def _iterElem(elem, recursive, tagName=None):
  """ Iterate over child elements, with the option to recurse down the tree and 
  match only elements with tagName.
  """
  child = elem.firstChildElement()
  while _isValidElem(child):
    if not tagName or child.tagName() == tagName:
      yield child
    if recursive:
      for grandchild in _iterElem(child, recursive, tagName):
        yield grandchild
    child = child.nextSiblingElement()


def _getElemGuid(elem):
  """ Extract the guid attribute from an element. Raises an exception if it wasn't found.
  """
  guid = elem.attribute('guid')
  if not guid:
    raise RuntimeError("Failed to find guid for elem %s" % elem.tagName())
  return guid


def _findElemByGuid(guid, path, root):
  """ Search for an element with the path from the root element which matches
  guid.
  """
  for elem in _findAllInElem(root, path):
    if elem.attribute('guid') == guid:
      return elem
  raise RuntimeError("Failed to find element with guid %s in path %s %s" % (guid, root, path))


def _findTrackItemByGuid(guid, root):
  """ Find a track item by guid from the document root. """
  return _findElemByGuid(guid, 'trackItemCollection/TrackItem', root)


def _findMediaSourceByGuid(guid, root):
  """ Find a media source by guid from the document root. """
  return _findElemByGuid(guid, 'Media/Source', root)


def _extractLookEffectParams(look):
  """ Extract the parameters from a Look element. Returns a dict of {name : value} """
  params = OrderedDict()
  for param in [e.firstChildElement() for e in _findAllInElem(look, 'Effect/values/EffectParameter')]:
    name = param.attribute('name')
    value = param.attribute('value')
    params[name] = value
  return params


def _quote(s):
  """ Wrap a string in quotes """
  return '"' + s + '"'

# Conversion functions for mapping effect parameters to knob values
def _convertNoOp(x): return x
def _convertBool(x): return 'true' if x == 'Yes' else 'false'
def _convertVector3(x): return '{' + x.replace(',', ' ') + '}'
def _convertR3DGain(x): return '{' + ' '.join(x) + '}'

def _convertDictLookup(_dict):
  def inner(x):
    return _quote( _dict[x] )
  return inner

def _convertListLookup(_list):
  def inner(x):
    return _quote( _list[int(x)] )
  return inner

# Maps of conversions from effect parameters to knobs. Each entry consists of:
# (parameter name(s), knob name, conversion function)
# Some conversions use more than one parameter to map to a single knob, in which
# case  the first entry is a tuple
_kLookParamToKnobDefinitionsShared = [
  ('colourspacename', 'colorspace', _quote),
]

# Knobs which are required by the r3dReader
_kRequiredKnobsR3D = [
  ('r3dSDK', '11'),
  ('r3dInit', '2'),
  ('r3dColorVersion', 'v2'),
]

# Effect parameter conversions for r3d files
_kLookParamToKnobDefinitionsR3D = _kLookParamToKnobDefinitionsShared + [
  # R3D params
  ('hdrBlendMode', 'r3dHDRMode',  _convertNoOp),
  ('hdrBias', 'hdr_bias', _convertNoOp),
  ('hdrTrack', 'r3dBlendBias', _convertNoOp),
  ('monitorColourSpace', 'r3dColorSpace', _convertDictLookup(_kR3DColorSpaces)),
  ('gammaSpace', 'r3dGammaCurve', _convertDictLookup(_kR3DGammaSpaces)),
  ('ISO', 'r3dISO', _convertNoOp),
  ('FLUT', 'r3dFlutControl', _convertNoOp),
  ('exposure', 'r3dExposure', _convertNoOp),
  ('contrast', 'r3dContrast', _convertNoOp),
  ('brightness', 'r3dBrightness', _convertNoOp),
  ('shadow', 'r3dShadow', _convertNoOp),
  ('DRX', 'r3dDRX', _convertNoOp),
  ('kelvin', 'r3dKelvin', _convertNoOp),
  ('tint', 'r3dTint', _convertNoOp),
  ('saturation', 'r3dSaturation', _convertNoOp),
  ('sharpness', 'r3dSharpness', _convertNoOp),
  ('denoise', 'r3dDenoise', _convertNoOp),
  ('debayer', 'r3dDetail', _convertNoOp),
  ('decodeMode', 'r3dDecodeResolution', _convertDictLookup(_kR3DDecodeModes)),
  (('red', 'green', 'blue'), 'r3dRGBGain', _convertR3DGain), # Note these are separate params in the hrox
  ('lift', 'r3dLift', R3DLggParamConverter(True)),
  ('gamma', 'r3dGamma', R3DLggParamConverter(False)),
  ('gain', 'r3dGain', R3DLggParamConverter(False)),
]

# Knobs which are required by the arriReader
_kRequiredKnobsArri = [
  ('ari_init', '1'),
  ('arri_sdk', '0'),
]

# Effect parameter conversions for Arri files
_kLookParamToKnobDefinitionsArri = _kLookParamToKnobDefinitionsShared + [
  ('iso', 'iso', _convertNoOp),
  ('color_temp', 'color_temp', _convertNoOp),
  ('tint', 'tint', _convertNoOp),
  ('color_space', 'arri_colorspace', _convertDictLookup(_kArriColourSpaces)),
  ('lens_squeeze', 'lens_squeeze', _convertListLookup(_kArriLensSqueeze)),
  ('apply_anamorph', 'apply_anamorph', _convertBool),
  ('aspect_ratio', 'aspect_ratio', _convertListLookup(_kArriAspectRatios)),
  ('resolution', 'resolution', _convertListLookup(_kArriResolutions)),
  ('proxy', 'proxy', _convertListLookup(_kArriProxyModes)),
  ('debayering_mode', 'debayering_mode', _convertListLookup(_kArriDebayeringMode)),
  ('fine_tuning_red', 'fine_tuning_red', _convertNoOp),
  ('fine_tuning_green', 'fine_tuning_green', _convertNoOp),
  ('fine_tuning_blue', 'fine_tuning_green', _convertNoOp),
  ('crispness', 'crispness', _convertNoOp),
  ('apply_look', 'apply_look', _convertBool),
  ('saturation', 'saturation', _convertNoOp),
  ('denoise_active', 'denoise_active', _convertBool),
  ('denoise_weight', 'denoise_weight', _convertNoOp),
  ('printer_lights', 'printer_lights', _convertVector3),
  ('slope', 'slope', _convertVector3),
  ('offset', 'offset', _convertVector3),
  ('power', 'power', _convertVector3),
]


def _mapLookParamsToKnobs(params, knobs, definitions):
  """ Convert any EffectParameter values to knob form, and add to the list of knobs """

  # Iterate over all known params and try to convert them
  for paramName, knobName, converter in definitions:
    try:
      # For cases where multiple params result in a single knob value, paramName will be a tuple,
      # extract them and pass to the converter function
      if isinstance(paramName, tuple):
        paramValues = [params[n] for n in paramName]
        knobs.append( (knobName, converter(paramValues)) )
      else:
        knobs.append( (knobName, converter(params[paramName])) )
    except KeyError:
      # This will occur if the param isn't present in the hrox, ignore it
      pass

def _filterDefaultColorspace(lookParams):
  """ The "default" colorspace of a clip's read node, does not
  need to be serialised. If it is missing, "default" will automatically
  be selected. Originally, serialising "default" confused Nuke 12.0+
  with the default OCIO role. Hence, the need for this filter.
  """
  csname_field = "colourspacename"
  if csname_field in lookParams:
    if lookParams[csname_field] == "default":
      del lookParams[csname_field]

def _cleanupLookElem(look):
  """ Cleanup the Look element for a TrackItem. TODO This should probably be
  removed completely, but for now we need to remove all the parameters apart from
  'colourspacename' otherwise problems occur in StormEffectProxy.
  """
  effectValues = _findFirstInElem(look, 'Effect/values')
  # For offline clips, sometimes the look doesn't have any effects
  if effectValues is None:
    return
  paramsToRemove = [param for param in _findAllInElem(effectValues, 'EffectParameter') if param.firstChildElement().attribute('name') != 'colourspacename']
  for param in paramsToRemove:
    effectValues.removeChild(param)


def _findClipFirstTrackItem(clip):
  """Find the clip's first track item and return the guid and whether it was video """
  try:
    trackItemGuid = _getElemGuid(_findFirstInElem(clip, 'videotracks/VideoTrack/trackItems/TrackItem'))
    return trackItemGuid, True
  except:
    trackItemGuid = _getElemGuid(_findFirstInElem(clip, 'audiotracks/AudioTrack/trackItems/TrackItem'))
    return trackItemGuid, False


def _clipKnobDefinitionsForPath(filePath):
  """ Get the knob definitions for the file type in filePath. Returns a tuple
  of (requiredKnobs, lookParamDefinitions)
  """
  _, ext = os.path.splitext(filePath)
  ext = ext.lower()
  isR3D = ext == '.r3d'
  isArri = ext in ('.ari', '.arri')
  if isR3D:
    return _kRequiredKnobsR3D, _kLookParamToKnobDefinitionsR3D
  elif isArri:
    return _kRequiredKnobsArri, _kLookParamToKnobDefinitionsArri
  else:
    return [], _kLookParamToKnobDefinitionsShared


_kPathFrameRangeRegEx = re.compile(' \\d+-\\d+$')

def _stripPathFrameRange(filePath):
  """ File sequence paths are stored in the hrox with the range on the end,
  strip this.
  """
  global _kPathFrameRangeRegEx
  return _kPathFrameRangeRegEx.sub('', filePath)


def _findMetadataValue(root, name):
  """ Search for a value in an element's metadata """
  values = _findFirstInElem(root, 'sets/Set/values')
  for child in _iterElem(values, False):
    if child.attribute('name') == name:
      return child.attribute('value')
  return None


def _createReadNodeElem(doc, knobs):
  """ Generate the script for a Read node and create an element from a list of
  knob name/values.
  """
  nodeScript = 'Read {\n' + '\n'.join(['%s %s' % (n, v) for n, v in knobs]) + '\n}'
  node = doc.createElement('node')
  node.appendChild(doc.createTextNode(nodeScript))
  return node


def _convertClipXml(clip, root):
  """ Convert clip xml to the new format. """
  # Fix the tag
  clip.setTagName('Clip')

  # Find the clip's first track item, inside the clip this is just a link to the
  # actual data elsewhere in the document
  trackItemGuid, isVideo = _findClipFirstTrackItem(clip)
  trackItem = _findTrackItemByGuid(trackItemGuid, root)

  # Find the MediaSource which contains the actual file path. Again, the track
  # item just links to the Source data
  mediaSrcGuid = _getElemGuid(_findFirstInElem(trackItem, 'MediaGroup/groupdata/MediaInstance_Vector/Source'))
  mediaSrc = _findMediaSourceByGuid(mediaSrcGuid, root)
  filePath = mediaSrc.attribute('file')
  filePath = _stripPathFrameRange(filePath)

  # Build a list of knobs to be added to the Read node
  readKnobs = []
  readKnobs.append( ('name', _quote(clip.attribute('name'))) )
  readKnobs.append( ('file', _quote(filePath)) )

  # If this is a video clip, extract all the effect parameters from the Look
  # element and map them to knob values
  if isVideo:
    # Set the frame range knobs. The starttime metadata doesn't always exist for
    # some reason, but in those cases it seems to be when it would have been 0,
    # so assume that's the case (not that we can do much else).
    try:
      starttime = int(_findMetadataValue(mediaSrc, 'foundry.source.starttime'))
    except:
      starttime = 0

    # Check for movie files which need to start at frame 1 on the Read node
    _, fileExt = os.path.splitext(filePath)
    if fileExt in _kNonZeroStartFrameMovieFileExtensions:
      starttime = 1

    duration = int(_findMetadataValue(mediaSrc, 'foundry.source.duration'))
    last = starttime + duration - 1
    readKnobs.append(('first', starttime))
    readKnobs.append(('origfirst', starttime))
    readKnobs.append(('last', last))
    readKnobs.append(('origlast', last))

    requiredKnobs, lookParamKnobDefs = _clipKnobDefinitionsForPath(filePath)
    readKnobs.extend(requiredKnobs)

    look = _findFirstInElem(trackItem, 'Look')
    lookParams = _extractLookEffectParams(look)
    _filterDefaultColorspace(lookParams)
    _mapLookParamsToKnobs(lookParams, readKnobs, lookParamKnobDefs)

    _cleanupLookElem(look)

  clip.appendChild(_createReadNodeElem(root.ownerDocument(), readKnobs))


def _convertExportPath(root):
  """ Converts the legacy per-project export root path setting to use the new
  form of the user choosing between the 'project directory' or setting a custom path. 
  """

  proj = _findFirstInElem(root, 'Project')

  if proj is None:
    return

  # Look for a user-specified export root path, the attribute will only exist if the
  # user set a non-empty path.
  exportPath = proj.attribute('exportRootPath')

  if exportPath:
    # We've found a (non-empty) export path attribute so need to set the new _custom_ export root
    # attribute and also set the mode to custom so that's what the application actually uses.
    proj.setAttribute('exportRootPathMode', 'CustomDirectory')
    proj.setAttribute('customExportRootPath', exportPath)
    # Remove the legacy attribute (there's no convenience function to do this).
    proj.removeAttribute('exportRootPath')
  else:
    # There was no export path set (or it was somehow set as an empty string) so just set the
    # new export root mode to default of using whatever the project directory is set to (which
    # may be nothing but that's irrelevant here). There's no point adding a customExportRootPath
    # attribute with an empty string.
    proj.setAttribute('exportRootPathMode', 'ProjectDirectory')


def _findClipElements(root, clips, links):
  """ Iterate over all 'Sequence' elements in the document. If they have the
  isclip="1" attribute, they're a clip and need to be converted. Also find any
  links (which may or may not reference clips), so the tag name can be updated to
  'Clip' if necessary.
  """
  for seq in _iterElem(root, True, 'Sequence'):
    if seq.attribute('isclip') == '1':
      clips.append(seq)
    elif seq.attribute('link') == 'internal':
      links.append(seq)


def _convertClipsAndLinks(root, clips, links):
  # Fix all the clips and build a list of their guids
  clipGuids = set()
  for clip in clips:
    clipGuids.add(_getElemGuid(clip))
    _convertClipXml(clip, root)

  # Fix the tag name on any links which point to a clip
  for link in links:
    guid = _getElemGuid(link)
    if guid in clipGuids:
      link.setTagName('Clip')


def _findAndConvertClips(root):
  """ Search for clip-related elements in the document and convert them. """
  # Find all clip related elements
  clips = []
  links = []
  _findClipElements(root, clips, links)

  # Convert the clip elements to the new format
  _convertClipsAndLinks(root, clips, links)


def _convertProjectXml(root):
  """ Convert the project XML to the new format, modifying the element tree
  structure in place.
  """
  # Set the project version
  root.setAttribute('version', _kToProjectVersion)

  # Handle the changes to export root path setting.
  _convertExportPath(root)

  # Find clips in the project and convert them
  _findAndConvertClips(root)


def _checkProjectVersion(root):
  """ Check the project version. If it's not a version that can be converted,
  throws a RuntimeError.
  """
  version = root.attribute('version')
  if version == _kToProjectVersion:
    raise RuntimeError("Project is already at current version!")
  elif version not in _kFromProjectVersions:
    raise RuntimeError("Don't know how to convert project at version %s" % version)


def _setProjectName(root, dstPath):
  """ Set the name on the project element. This is expected to be the same as
  hrox file name.
  """
  name = os.path.splitext(os.path.basename(dstPath))[0]
  proj = _findFirstInElem(root, 'Project')
  proj.setAttribute('name', name)


def _convertLegacyHroxDocument(root, dstPath):
  """ Read hrox XML data from a file object, convert it and write back to a file object.
  dstPath is the path the file will be written to, which is used for putting the
  project's name into the XML
  """
  # Check the project can be converted. This will throw if it fails
  _checkProjectVersion(root)

  # Set the attribute for the Nuke release to the current
  root.setAttribute('release', _kCurrentVersionString)

  # Convert the project xml to the new format
  _convertProjectXml(root)

  # Set the project name to match the destination path
  if dstPath:
    _setProjectName(root, dstPath)


def convertLegacyHroxString(srcStr, dstPath):
  """ Convert hrox XML data stored in a string, and return the result as a string.
  dstPath is the path the file will be written to, which is used for putting the
  project's name into the XML
  """
  doc = QDomDocument()
  doc.setContent(srcStr)
  _convertLegacyHroxDocument(doc.documentElement(), dstPath)
  return doc.toByteArray()


def convertLegacyHroxFile(srcPath, dstPath):
  """ Convert an hrox file to the format used by Nuke 11.1 (and later). Throws
  if there are any errors.
  """
  srcFile = QFile(srcPath)
  if not srcFile.open(QFile.ReadOnly):
    raise RuntimeError("Failed to open source file %s" % srcPath)
  doc = QDomDocument()
  doc.setContent(srcFile)
  srcFile.close()
  _convertLegacyHroxDocument(doc.documentElement(), dstPath)

  dstFile = QFile(dstPath)
  if not dstFile.open(QFile.WriteOnly):
    raise RuntimeError("Failed to open destination file %s" % dstPath)
  stream = QTextStream(dstFile)
  doc.save(stream, 1)
  dstFile.close()


if __name__ == '__main__':
  srcPath = sys.argv[1]
  dstPath = sys.argv[2]
  convertLegacyHroxFile(srcPath, dstPath)

