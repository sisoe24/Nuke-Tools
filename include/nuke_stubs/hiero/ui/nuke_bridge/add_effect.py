import hiero.ui
import hiero.core
import sys
import os
from .send_to_nuke import SendToNukeHandler
from hiero.core import log
from hiero.ui import registerAction
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QAction, QMenu

gNukeIconPath = os.path.join(os.path.dirname(sys.executable),"plugins","icons")


def createEffectActions():
  # Create the actions which should be added to the Effect button on the toolbar of the timeline view.
  # It will look for any actions which match foundry.timeline.effect.*
  # To have it create a soft effect we call setData with the node type.
  action = QAction(QIcon(gNukeIconPath + "/2D.png"), "Transform", None)
  action.setObjectName("foundry.timeline.effect.addTransform")
  action.setToolTip("Transform")
  action.setData("Transform")
  registerAction(action)

  action = QAction(QIcon(gNukeIconPath + "/Mirror.png"), "Mirror", None)
  action.setObjectName("foundry.timeline.effect.addMirror")
  action.setToolTip("Mirror")
  action.setData("Mirror2")
  registerAction(action)

  action = QAction(QIcon(gNukeIconPath + "/Crop.png"), "Crop", None)
  action.setObjectName("foundry.timeline.effect.addCrop")
  action.setToolTip("Crop")
  action.setData("Crop")
  registerAction(action)

  action = QAction(QIcon(gNukeIconPath + "/TimeWarp.png"), "Timewarp", None)
  action.setObjectName("foundry.timeline.effect.addTimewarp")
  action.setToolTip("Timewarp")
  action.setData("TimeWarp")
  registerAction(action)

  action = QAction(QIcon(gNukeIconPath + "/Grade.png"), "Grade", None)
  action.setObjectName("foundry.timeline.effect.addGrade")
  action.setToolTip("Grade")
  action.setData("Grade")
  registerAction(action)

  action = QAction(QIcon("icons:LUT.png"), "LUT", None)
  action.setObjectName("foundry.timeline.effect.addOCIOFileTransform")
  action.setToolTip("LUT")
  action.setData("OCIOFileTransform")
  registerAction(action)

  action = QAction(QIcon( gNukeIconPath + "/OCIO.png"), "CDL", None)
  action.setObjectName("foundry.timeline.effect.addOCIOCDLTransform")
  action.setToolTip("CDL")
  action.setData("OCIOCDLTransform")
  registerAction(action)

  action = QAction(QIcon( gNukeIconPath + "/ColorSpace.png"), "Colorspace", None)
  action.setObjectName("foundry.timeline.effect.addOCIOColorSpace")
  action.setToolTip("ColorSpace")
  action.setData("OCIOColorSpace")
  registerAction(action)

  action = QAction(QIcon(gNukeIconPath + "/ColorCorrect.png"), "ColorCorrect", None)
  action.setObjectName("foundry.timeline.effect.addColorCorrect")
  action.setToolTip("ColorCorrect")
  action.setData("ColorCorrect")
  registerAction(action)

  action = QAction(QIcon(gNukeIconPath + "/Text.png"), "Text", None)
  action.setObjectName("foundry.timeline.effect.addText")
  action.setToolTip("Text")
  action.setData("Text2")
  registerAction(action)

  action = QAction(QIcon(gNukeIconPath + "/BurnIn.png"), "Burn-In", None)
  action.setObjectName("foundry.timeline.effect.addBurnIn")
  action.setToolTip("Burn-In")
  action.setData("BurnIn")
  registerAction(action)

  action = QAction(QIcon(gNukeIconPath + "/ChromaKeyer.png"), "ChromaKeyer", None)
  action.setObjectName("foundry.timeline.effect.ChromaKeyer")
  action.setToolTip("ChromaKeyer")
  action.setData("ChromaKeyer")
  registerAction(action)

  action = QAction(QIcon(gNukeIconPath + "/BlinkScript.png"), "BlinkScript", None)
  action.setObjectName("foundry.timeline.effect.BlinkScript")
  action.setToolTip("BlinkScript")
  action.setData("BlinkScript")
  registerAction(action)

def createEffectActionsStudio():
  action = QAction(QIcon("icons:Nuke.png"), "Create Comp", None)
  action.setObjectName("foundry.timeline.effect.createComp")
  action.setToolTip("Create Comp")
  action.setEnabled(False)
  registerAction(action)

  action = QAction(QIcon("icons:Nuke.png"), "Create Comp Special...", None)
  action.setObjectName("foundry.timeline.effect.createCompSpecial")
  action.setToolTip("Create Comp Special")
  action.setEnabled(False)
  registerAction(action)
  
  createEffectActions()
  

class AddEffectHandler( SendToNukeHandler ):
  def __init__(self, hieroState):
    log.debug ( 'add effect handler' )

    SendToNukeHandler.__init__(self, hieroState )

    fileMenu = hiero.ui.findMenuAction("foundry.menu.file")
    # Connect to the global 'Add Effect' action, which is added to the timeline toolbar
    createCompGlobalAction = hiero.ui.findRegisteredAction("foundry.timeline.effect.createComp")
    createCompSpecialAction = hiero.ui.findRegisteredAction("foundry.timeline.effect.createCompSpecial")
    if createCompGlobalAction:
      createCompGlobalAction.triggered.connect( self.onCreateComp )
      hiero.ui.insertMenuAction(createCompGlobalAction,
                                fileMenu.menu(),
                                after="foundry.project.export")

    if createCompSpecialAction:
      createCompSpecialAction.triggered.connect( self.onCreateCompSpecial )
      hiero.ui.insertMenuAction(createCompSpecialAction,
                                fileMenu.menu(),
                                after="foundry.project.export")
    

  def onCreateComp(self):
    from . create_comp import CreateCompAction
    """ Callback from the global 'Add Effect' action. """
    activeSequence = hiero.ui.activeSequence()
    timelineEditor = hiero.ui.getTimelineEditor(activeSequence)
    if timelineEditor:

      selection = timelineEditor.selection()
      if selection:
        action = self.makeCreateCompAction(selection, CreateCompAction)
        action.doit()


  def onCreateCompSpecial(self):
    from . create_comp import CreateCompSpecialAction
    activeSequence = hiero.ui.activeSequence()
    timelineEditor = hiero.ui.getTimelineEditor(activeSequence)
    if timelineEditor:
      selection = timelineEditor.selection()
      if selection:
        action = self.makeCreateCompAction(selection, CreateCompSpecialAction)
        action.doit()


  def makeCreateCompAction(self, selection, objectType):
    """ Create an CreateCompAction from the given selection, and return it """
    # only handle selections of trackitems, clips, and sequence items
    clips = []
    sequences = []
    trackItems = []
    effectItems = []
    bins = []
    annotations = []
    self._findItems(selection, clips, sequences, trackItems, bins, effectItems, annotations)
    return objectType(trackItems, effectItems, annotations, title="Create Comp")


  ## override
  def binContextMenuEventHandler(self, event):
    pass


  ## override
  def timelineContextMenuEventHandler(self, event):

    # reset our list of actions
    self._actions = []

    timelineEditor = event.sender
    selection = timelineEditor.selection()

    # only add if there's a selection to handle, and it's a sequence (not a clip) that's being edited
    if selection and timelineEditor.sequence():
      # create a Nuke sub menu
      event.menu.addSeparator()
      effectsMenu = event.menu.addMenu( "Effects" )
      for action in hiero.ui.findRegisteredActions( 'foundry.timeline.effect.' ):
        effectsMenu.addAction( action )


