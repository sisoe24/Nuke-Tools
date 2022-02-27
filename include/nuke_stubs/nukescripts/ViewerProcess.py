import nuke
import ocionuke
import os


def _setOCIOConfig(configPath):
  '''
  Set the OCIO Config to use the specified config path, unless
  the OCIO environment variable is defined, in which case that will
  override configPath. Otherwise if configPath is None then the nuke
  default config is used. If configPath doesn't exist an IOError is raised.
  '''
  rootNode = nuke.root()
  ocioConfigKnob = rootNode.knob("OCIO_config")

  # When the OCIO env var is set the OCIO knobs are disabled
  canChangeConfig = ocioConfigKnob.enabled()
  if canChangeConfig:
    # The root node handles checking whether the OCIO envvar needs to be used
    # or not. This check is performed whenever the OCIO knobs are changed, so
    # isn't needed here.
    useDefaultNukeConfig = configPath == ""
    if useDefaultNukeConfig:
      ocioConfigKnob.setValue("nuke-default")
    else:
      if os.path.exists(configPath):
        ocioConfigKnob.setValue("custom")
        customOCIOConfigPathKnob = rootNode.knob("customOCIOConfigPath")
        customOCIOConfigPathKnob.setText(configPath)
      else:
        raise IOError("Config '%s' doesn't exist" % configPath)


# Maintaining this function for backwards compatability
def getDefaultOCIOConfig(ocioConfigName = ""):
  _setOCIOConfig(ocioConfigName)


def register_default_viewer_processes():

  # The ViewerProcess_None gizmo is a pass-through -- it has no effect on the image.
  nuke.ViewerProcess.register("None", nuke.createNode, ("ViewerProcess_None", ))
# The ViewerProcess_1DLUT gizmo just contains a ViewerLUT node, which
  # can apply a 1D LUT defined in the project LUTs. ViewerLUT features both
  # software (CPU) and GPU implementations.

  nuke.ViewerProcess.register("sRGB", nuke.createNode, ( "ViewerProcess_1DLUT", "current sRGB" ))
  nuke.ViewerProcess.register("rec709", nuke.createNode, ( "ViewerProcess_1DLUT", "current rec709" ))
  # NOTE: If you change this mapping you'll need to update FlipbookDialog._getBurninWriteColorspace.
  nuke.ViewerProcess.register("rec1886", nuke.createNode, ( "ViewerProcess_1DLUT", "current Gamma2.4" ))


def unregister_viewers(ocioConfigPath):
  ocioConfig = ocionuke.config.loadConfig(ocioConfigPath)

  # unregister all OCIO LUTS
  # For every display, loop over every view
  DISPLAY_UI_FORMAT = "%(view)s (%(display)s)"
  for display in ocioConfig.getDisplays():
    for view in ocioConfig.getViews(display):
      # Unregister the node
      name = DISPLAY_UI_FORMAT % {'view': view, "display": display}
      nuke.ViewerProcess.unregister(name)


def _register_viewer_processes(defaultLUTS, ocioConfigName, also_remove, isReload):
  if defaultLUTS is True:
    # register the default viewer processes
    register_default_viewer_processes()
  else:
    # register OCIO viewer processes
    ocionuke.viewer.register_viewers(ocioConfigName, also_remove, isReload)


def register_viewers(defaultLUTS = True, ocioConfigName = ""):

  ocioConfigName = os.path.normpath(ocioConfigName).replace("\\", "/")

  # make sure we register the config before we begin
  _setOCIOConfig(ocioConfigName)

def storeViewerProcessSelectionBeforeReload():
  ocionuke.viewer.storeSelectionBeforeReload()
