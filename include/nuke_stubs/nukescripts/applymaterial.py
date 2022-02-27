"""Functions used by the ApplyMaterial node"""

import nuke
import nukescripts.panels


class ObjectNameChooserDialog(nukescripts.panels.PythonPanel):
  """A dialog box with a SceneView_Knob for choosing from a tree of names.

  The easiest way to use this is via the chooseObjectName function from this
  module, e.g.:

    chooseObjectName(["/root/foo", "/root/bar", "/root/bar/baz"])

  This will create and display the dialog as a modal popup and give you the
  selected name, or None if cancel was pressed.
  """

  def __init__(self, names):
    nukescripts.panels.PythonPanel.__init__( self, "Object Name Chooser", "uk.co.thefoundry.ObjectNameChooserDialog" )
    self.sceneView = nuke.SceneView_Knob("sceneView", "object name", names)
    self.addKnob(self.sceneView)
    self.setMinimumSize( 420, 50 )

  def selectedName(self):
    """Get the name selected in the SceneView_Knob."""
    return self.sceneView.getHighlightedItem()


def chooseObjectName(amfNode):
  """Given an ApplyMaterial node, show a modal ObjectNameChooserDialog
  for it then set the filter_name knob to whatever name was selected in the
  dialog.
  """
  if amfNode.Class() != "ApplyMaterial":
    raise Exception("%s is not an ApplyMaterial node" % amfNode.name())

  geoList = amfNode['geo_select'].getGeometry()
  names = [_getName(geo) for geo in geoList]
  dlg = ObjectNameChooserDialog(names)
  result = dlg.showModalDialog()
  if result:
    name = dlg.selectedName()
    name = _workaroundForBug36107(name, names) # Work around for Bug 36107 - SceneView_Knob trims leading '/' from strings. Remove this when that bug is fixed.
    amfNode['filter_name'].setValue(name)


def _getName(geo):
  """Given a GeoInfo object, return the value of its 'name' attribute. If there is no such attribute, return None."""
  attrCtx = geo.attribContext('name', 3, 7) # 3 = per-object attribute, 7 = std::string type
  if attrCtx is None:
    attrCtx = geo.attribContext('name', 3, 6) # 3 = per-object attribute, 6 = c-string (char*) type
  if attrCtx is not None:
    attr = attrCtx.attribute
    if attr is not None and len(attr) > 0:
      return attr[0]
  return None


def _workaroundForBug36107(name, names):
  if name is not None and name not in names:
    fixedName = '/' + name
    if fixedName in names:
      return fixedName
  return name

