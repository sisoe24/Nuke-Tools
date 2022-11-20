import hiero.core
from hiero.core.nuke import ReformatNode


# Default values for Reformat node knobs
kReformatDefaults = {
  "scale" : 1.0,
  "resize" : ReformatNode.kResizeWidth,
  "center" : True,
  "filter" : "Cubic",
}


def reformatSettingsFromPreset(preset):
  """ Extract the reformat properties from a task preset.  If the reformat type is 'to format', the format returns the format,
      if it's 'scale' returns the scale value. """
  type, format, scale, resize, center, filter = None, None, None, None, None, None

  rf = preset.properties()["reformat"]
  type = str(rf["to_type"])
  filter = str(rf.get("filter", kReformatDefaults["filter"]))
  if type in (ReformatNode.kToFormat, ReformatNode.kToScale, ReformatNode.kCompReformatToSequence):
    resize = rf.get("resize", kReformatDefaults["resize"])

  if type == ReformatNode.kToFormat:
    if "width" in rf and "height" in rf and "pixelAspect" in rf and "name" in rf and "resize" in rf:
      format = hiero.core.Format(rf["width"], rf["height"], rf["pixelAspect"], rf["name"])
      center = rf["center"]
    else:
      raise RuntimeError("reformat mode set to kToFormat but preset properties do not contain required settings.")
  elif type == ReformatNode.kToScale:
    if "scale" in rf:
      scale = float(rf["scale"])
      center = rf["center"]
    else:
      raise RuntimeError("reformat mode set to kToScale but preset properties do not contain required settings.")

  return type, format, scale, resize, center, filter


# Fixed values for knobs on created Reformat nodes.
__reformatKnobFixedValues = { "pbb" : True, "black_outside" : True }


def reformatNodeFromPreset(preset, sequenceFormat, trackItem=None):
  """ If reformat options are configured in the preset, return a ReformatNode
  created from them. Otherwise returns None.
  @param sequenceFormat: Specifies the sequence format.  Used only when preset
  specifies reformatting to sequence format
  @param trackItem: item from which to take the reformat settings when
  to sequence format is specified.
  """
  # Get the reformat settings
  type, format, scale, resize, center, filter = reformatSettingsFromPreset(preset)

  # Check for valid type settings
  if type not in (ReformatNode.kToFormat, ReformatNode.kToScale, ReformatNode.kCompReformatToSequence):
    return None

  # If 'To Sequence' is specified, and a track item was given, get the resize
  # type and center from its reformat state.
  if type == ReformatNode.kCompReformatToSequence and trackItem:
    reformatState = trackItem.reformatState()
    if reformatState.type() == ReformatNode.kDisabled:
      center = True
      resize = ReformatNode.kResizeNone
    else:
      center = reformatState.resizeCenter()
      resize = reformatState.resizeType()

  # Create a dict with the knob values, and return a ReformatNode with it.
  reformatKnobs = dict()
  reformatKnobs.update(__reformatKnobFixedValues)

  reformatKnobs["resize"] = resize
  reformatKnobs["center"] = center
  reformatKnobs["filter"]= filter
  if type == ReformatNode.kToScale:
    reformatKnobs["to_type"] = ReformatNode.kToScale
    reformatKnobs["scale"] = scale
  else:
    reformatKnobs["to_type"] = ReformatNode.kToFormat
    if type == ReformatNode.kToFormat:
      reformatKnobs["format"] = str(format)
    elif type == ReformatNode.kCompReformatToSequence:
      reformatKnobs["format"] = str(sequenceFormat)

  return ReformatNode(**reformatKnobs)
