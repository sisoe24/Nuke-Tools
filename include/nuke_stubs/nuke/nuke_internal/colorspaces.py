"""
A collection of tools and functions to help manage LUTs and color configuration
"""
from _nuke_color import * # bring the libnuke PythonAPI for color into scope
from . import callbacks
import types
import nuke_internal as nuke

defaultLUTMappers = {} # dictionary of all mappers

class ColorspaceLookupError(Exception):
  """ an excpetion that should be thrown when looking up the colorspace """
  pass


def _attemptColorspaceNameMatch(colorspaceName) :
  """ Look through all options in the colorpsace knob, and see if we have an
  exact match to one of the items. """
  node = nuke.thisNode()
  try:
    colorspaceKnob = node['colorspace']
  except ValueError:
    # failed to get the Knob from the Node because the Node may be unattached
    # when loading script or similar
    return False
  allColorspaces = getColorspaceList( colorspaceKnob )
  return colorspaceName in allColorspaces


def _lookUpDataTypeDefaultSettings(colorspaceName, dataTypeHint):
  """
  Nuke's default handling of colorspace lookups.

  Maps applicable dataTypeHint values to knobs on the Preferecne panel

  Possible values for dataTypeHint are
    Nuke inbuilt data-type hints (map to knobs)
      nuke.MONITOR == 0
      nuke.VIEWER  == 1
      nuke.INT8    == 2
      nuke.INT16   == 3
      nuke.LOG     == 4
      nuke.FLOAT   == 5
    Other numeric values which map to those in DDImage/LUT.h
      6  == DD::Image::LUT::GAMMA1_8
      7  == DD::Image::LUT::GAMMA2_2
      8  == DD::Image::LUT::GAMMA2_4
      9  == DD::Image::LUT::PANALOG
      10 == DD::Image::LUT::REDLOG
      11 == DD::Image::LUT::VIPERLOG
      12 == DD::Image::LUT::ALEXAV3LOGC
      13 == DD::Image::LUT::PLOGLIN
      14 == DD::Image::LUT::SLOG
      15 == DD::Image::LUT::SLOG1
      16 == DD::Image::LUT::SLOG2
      17 == DD::Image::LUT::SLOG3
      18 == DD::Image::LUT::CLOG
      19 == DD::Image::LUT::PROTUNE
      20 == DD::Image::LUT::GAMMA2_6
      21 == DD::Image::LUT::LOG3G10
      22 == DD::Image::LUT::LOG3G12
      23 == DD::Image::LUT::BT1886
      24 is deprecated and shouldn't be used
      25 == DD::Image::LUT::HYBRIDLOGGAMMA
      26 == DD::Image::LUT::ST2084
  """

  root = nuke.thisRoot()

  def getKnobValue( knobName ) :
    try:
      knob = root[ knobName ]
    except ValueError:
      raise ColorspaceLookupError
    return knob.value()

  retString = colorspaceName
  if dataTypeHint   == nuke.MONITOR: #  0 = LUT::MONITOR
    retString =  getKnobValue( "monitorLut" )
  elif dataTypeHint == nuke.VIEWER: #  1 = LUT::VIEWER
    pass
  elif dataTypeHint == nuke.INT8: #  2 = LUT::INT8
    retString =  getKnobValue( "int8Lut" )
  elif dataTypeHint == nuke.INT16: #  3 = LUT::INT16
    retString =  getKnobValue( "int16Lut" )
  elif dataTypeHint == nuke.LOG: #  4 = LUT::LOG
    retString =  getKnobValue( "logLut" )
  elif dataTypeHint == nuke.FLOAT: #  5 = LUT::FLOAT
    retString =  getKnobValue( "floatLut" )
  return retString


def _nukeDefaultColorSpaceMapper(colorspaceName, dataTypeHint):
  """
  Allows colorspaces selections to be altered before use on Readers and Writers
  """
  if colorspaceName == "." :
    raise RuntimeError( "Nuke has provided invalid colorspace name" )
  try:
    retName = _lookUpDataTypeDefaultSettings(colorspaceName, dataTypeHint)
  except ColorspaceLookupError:
    retName = colorspaceName
  # TODO: find best name in colosrpace
  return retName


def addDefaultColorspaceMapper(call, args=(), kwargs={}, nodeClass='*'):
  """
  Add a function to modify default colorspaces before Nuke passes them to
  Readers or Writers.

  Functions should have the same positional argument as in the definition of
  defaultLUTMapper()

  All added functions are called in backwards order.
  """
  callbacks._addCallback(defaultLUTMappers, call, args, kwargs, nodeClass)


def removeDefaultColorspaceMapper(call, args=(), kwargs={}, nodeClass='*'):
  """
  Remove a previously-added callback with the same arguments.
  """
  callbacks._removeCallback(defaultLUTMappers, call, args, kwargs, nodeClass)


def _doColorSpaceCallbacks( colorspace, dataTypeHint, callbacks, errorMsg ) :
  """
  Perform the colorspace callbacks
  expects a string or 'None' to be returned.
  """
  for funcData in callbacks:
    func = funcData[0]
    args = funcData[1]
    kwargs = funcData[2]
    s = func(colorspace, dataTypeHint, *args, **kwargs)
    if not isinstance(s, str) and s is not None:
      raise TypeError( errorMsg + ". Got type %s"%str(type(s)) )
    if s is not None:
      colorspace = s
  return colorspace


def defaultColorspaceMapper(colorspace, dataTypeHint):
  """
  Called by libnuke.
  Calls into Node-level callbacks first, then global callbacks

  Arguments:
      colorspace   - the name string of the initial colorspace
      dataTypeHint - sometimes Readers/Writer request the default for a
                     particular data-type, i.e. int8, in16, float, etc.
  Return:
      The return should be the transformed/modified colorspace name.
      None is the same as returning the string unchanged.
  """
  import __main__

  # Do Nuke's in built mapping first.
  colorspace = _nukeDefaultColorSpaceMapper(colorspace, dataTypeHint)

  # Then do callbacks registered for this Node type
  colorspaceCbs = defaultLUTMappers.get(nuke.thisClass())
  if colorspaceCbs:
    nodeErrMsg = ( "Colorspace Filter on Node '%s' returned invalid type,"
                   "expected string or None"%( nuke.thisClass() ) )
    colorspace = _doColorSpaceCallbacks( colorspace, dataTypeHint, colorspaceCbs, nodeErrMsg )

  # Do global manipulations afterwards
  globalCbs = defaultLUTMappers.get('*')
  if globalCbs:
    globalErrMsg = ( "Global Colorspace Filter returned invalid type,"
                   "expected string or None" )
    colorspace = _doColorSpaceCallbacks( colorspace, dataTypeHint, globalCbs, globalErrMsg )
	
  return colorspace

def getColorspaceList(colorspaceKnob) :
  """
  Get a list of all colorspaces listed in an enumeration knob.
  This will strip family names if the knob has the STRIP_CASCADE_PREFIX flag set.
  """
  
  allColorspaces = list(colorspaceKnob.values())
  strippedColorspaces = []

  if not colorspaceKnob.getFlag(nuke.STRIP_CASCADE_PREFIX) :
    return allColorspaces
  else:
    for strippedColorspace in allColorspaces:
      # Strip up until the last '/', which represents the family name
      strippedColorspace = strippedColorspace.split('/')[-1]
      strippedColorspaces.append(strippedColorspace)

  return strippedColorspaces
