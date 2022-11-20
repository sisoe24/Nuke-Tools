import hiero.ui
import hiero.core
import nuke_internal as nuke
import nukescripts
from PySide2 import (QtCore, QtWidgets)
from . import hiero_state
import hiero.core.nuke
import os.path
from hiero.ui import findMenuAction, findRegisteredAction
from hiero.core.FnCompSourceInfo import isNukeScript
from hiero.core import util

isPlayer = hiero.core.isHieroPlayer();

if not isPlayer:
  from . import add_effect
  from hiero.ui.nuke_bridge import initFrameServer
  from hiero.exporters import FnFrameServerRender
  add_effect.createEffectActions()
  nukescripts.createNodePresetsMenu()


# declare some global variables
# note that these have to be global, so that references to them are kept around and don't get garbage collected

hieroState = None
addEffectHandler = None
eventHandler = None

localisation = findRegisteredAction("foundry.menu.localizationNuke")
timelineAction = findMenuAction("foundry.menu.cache")
timelineAction.menu().removeAction(localisation)


class OpenInNukeAction(QtWidgets.QAction):

  def __init__(self, hieroEventHandler):
    QtWidgets.QAction.__init__(self, "New Nuke Session", None)

    self.triggered.connect(self.doOpen)
    self.hieroEventHandler = hieroEventHandler
    hiero.core.events.registerInterest("kShowContextMenu/kTimeline", self.eventHandler)
    hiero.core.events.registerInterest("kShowContextMenu/kBin", self.eventHandler)

  def doOpen(self):

    filePath = self.hieroEventHandler.getNukeScriptPathFromItem( self.shotSelection[0] )

    if filePath:
      self.hieroEventHandler.openNuke( filePath )


  def eventHandler(self, event):
    if not hasattr(event.sender, 'selection'):
      # Something has gone wrong, we should only be here if raised
      # by the timeline view which will give a selection.
      return

    self.shotSelection = [item for item in event.sender.selection() if ( isinstance(item,hiero.core.TrackItem) or isinstance(item, hiero.core.BinItem) )]

    if len(self.shotSelection) != 1:
      return

    filePath = self.hieroEventHandler.getNukeScriptPathFromItem( self.shotSelection[0] )

    if not filePath:
      return

    for a in event.menu.actions():
      if a.text().lower().strip() == "open in":
        hiero.ui.insertMenuAction( self, a.menu(), before = "foundry.project.openInViewer" )


class HieroEventHandler:
  def __init__(self):
    # Listen for double click events, so we can open the DAG from double clicking in the timeline and bin view
    hiero.core.events.registerInterest((hiero.core.events.EventType.kDoubleClick, hiero.core.events.EventType.kBin), self.onDoubleClick)
    hiero.core.events.registerInterest((hiero.core.events.EventType.kDoubleClick, hiero.core.events.EventType.kTimeline), self.onDoubleClick)
    # Instantiate the action to get it to register itself.
    openInNewNukeAction = OpenInNukeAction(self)

  def getNukeScriptPathFromItem( self, item ):
    """ Extract the path from the given item, and check if it points to a Nuke script.
        Returns None if no path was found or if it wasn't a Nuke script. """
    filePath = None
    try:
      if isinstance(item, hiero.core.TrackItem) and isinstance(item.source(), hiero.core.Clip):
        clip = item.source()
      elif isinstance(item, hiero.core.BinItem):
        clip = item.activeVersion().item()
      elif hasattr(item, 'activeItem'):
        item = item.activeItem()
        if isinstance(item, hiero.core.Clip):
          clip = item
      if clip:
        filePath = clip.mediaSource().firstpath()

      # Check if the path exists and points to a Nuke script
      if not util.filesystem.exists(filePath) or not isNukeScript(filePath):
        filePath = None

    except Exception as e:
      pass

    return filePath

  def onDoubleClick(self, event):
    # Double click event from bin or timeline views.

    if not event.modifiers & QtCore.Qt.ControlModifier:
      return

    try:
      # Find the clicked clip.  If a track item was clicked on, we can get its clip source,
      # otherwise it should be a bin item
      filePath = self.getNukeScriptPathFromItem( event.item )

      if filePath:
        self.openNuke(filePath)

    except Exception as e:
      print(traceback.format_exc())

  def openNuke(self, filePath):
    """ Open a script in new Nuke process
        The caller should make sure the filePath is actually a valid Nuke script. """
    if filePath is not None:
      hiero.core.nuke.Script.launchNuke( filePath )
    return


def setup():
  global hieroState
  global addEffectHandler
  global eventHandler

  # initialize our state management object
  hieroState = hiero_state.HieroState()

  if not isPlayer:
    # create our event handler object
    addEffectHandler = add_effect.AddEffectHandler(hieroState)

  eventHandler = HieroEventHandler()

QtCore.QTimer.singleShot(0, setup)

