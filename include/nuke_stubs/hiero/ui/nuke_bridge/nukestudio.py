import nuke_internal as nuke

if nuke.env['hiero']:
  raise ImportError("nukestudio should not be imported in Hiero")
elif not nuke.env['studio']:
  raise ImportError("nukestudio should not be imported in Nuke")

import hiero.ui
import hiero.core
import os, os.path, sys
import signal
from PySide2 import (QtCore, QtGui, QtWidgets)
from . import hiero_state
from . import add_effect
import threading
import traceback
import time
import foundry.ui
import nukescripts

from _fnpython import menuBar, currentWorkspace
from hiero.ui import findMenuAction, insertMenuAction
import hiero.core.nuke
from hiero.core import util
from hiero.core.FnCompSourceInfo import isNukeScript
from hiero.ui.nuke_bridge import add_effect
import hiero.ui.nuke_bridge.initNuke
from hiero.exporters import FnFrameServerRender

add_effect.createEffectActionsStudio()

# declare some global variables
# note that these have to be global, so that references to them are kept around and don't get garbage collected
hieroState = None
addEffectHandler = None
eventHandler = None


def scriptSaveAndReRender():
  """ Save the current nk script and queue background re-render of its frames. """
  nuke.scriptSave()
  if not autoBackgroundRenderOnScriptSave():
    name = nuke.scriptName()
    if name:
      hiero.ui.nuke_bridge.FnNsFrameServer.renderScript(name)


def makeScriptSaveAndReRenderAction():
  action = QtWidgets.QAction("Save Comp And Rerender", None)
  action.setObjectName("foundry.project.savererender")
  # TODO Add shortcut
  action.triggered.connect(scriptSaveAndReRender)
  return action


# Constants which match the values defined in fnPreferences.h
kAutoBackgroundRenderPrefKey = "frameserver/backgroundrenderautostart"
kAutoBackgroundRenderNeverValue = 0
kAutoBackgroundRenderOnSaveValue = 1
kAutoBackgroundRenderOnSaveCreateOrVersionValue = 2


def autoBackgroundRenderOnScriptSave():
  """ Check if a script should be automatically re-rendered when the user saves normally. """

  settings = hiero.core.ApplicationSettings()
  prefValue = int(settings.value(kAutoBackgroundRenderPrefKey))
  return (prefValue != kAutoBackgroundRenderNeverValue)

def addNewScriptVersionToBinRec(bin, previousFileName, newFileName):
  for clip in bin.clips():
    versions = list(clip.items())
    for version in versions:
      source = version.item().mediaSource()
      if (source is not None and source.fileinfos() is not None):
        try:
          versionFile = source.fileinfos()[0].filename()
        except IndexError:
          # Transform an index error into a MediaFileInfo error.
          # Please see TP #422874 for details.
          raise NotImplementedError('MediaFileInfo is missing.  This may be '
                                    'due to unimplemented video file '
                                    'rendering.  Please ensure that the script '
                                    'is writing to an image sequence.')

        if (versionFile == previousFileName):
          scanner = hiero.core.VersionScanner.VersionScanner()
          scanner.insertVersions(clip, [newFileName] )
          return True

  for subbin in bin.bins():
    if addNewScriptVersionToBinRec(subbin, previousFileName, newFileName):
      return True

def addNewScriptVersionToBin(previousFileName, newFileName):
  projects = hiero.core.projects()
  #iterate over all the bin items and find the version that contains the mediasource with the filename
  #if we find a version containing a mediasource with the old version filename add the new one
  for project in projects:
    addNewScriptVersionToBinRec(project.clipsBin(), previousFileName, newFileName)


# These also have to be global to stop them getting eaten by the GC
nukeMenuBar = nuke.menu('Nuke')
nukeOpenItem = nukeMenuBar.findItem("File/Open Comp...")
nukeCloseItem = nukeMenuBar.findItem("File/Close Comp")
nukeSaveItem = nukeMenuBar.findItem("File/Save Comp")
nukeSaveAsItem = nukeMenuBar.findItem("File/Save Comp As...")
nukeUndoItem = nukeMenuBar.findItem("Edit/Undo")
nukeRedoItem = nukeMenuBar.findItem("Edit/Redo")
hieroUndoItem = findMenuAction("foundry.application.undo")
hieroRedoItem = findMenuAction("foundry.application.redo")
saveAndReRenderAction = makeScriptSaveAndReRenderAction()
recentNukeActions = []

def insertNukeAction(item, menu, before = None, after = None, context = hiero.ui.kContextStudio):
  assert item is not None, "item passed into insertNukeAction is None"
  assert menu is not None, "menu passed into insertNukeAction is None"
  insertAction(item.action(), menu, before, after, context)
  item.setVisible(True)
  item.setEnabled(True, True)

def insertAction(action, menu, before = None, after = None, context = hiero.ui.kContextStudio):
  assert action is not None, "action passed into insertAction is None"
  assert menu is not None, "menu passed into insertAction is None"
  insertMenuAction(action, menu, before, after)
  setContext(action, context, True)


# Call updateMenuItems to ensure the nuke action states are updated before showing the menu
def aboutToShowMenu():
  nukeMenuBar.updateMenuItems()

# Helper function to resolve duplicate menus. Will set the nuke one to
# be visible only in comp layout and the hiero to be only visible in timeline
# layout. Places the menus next to each other.
def initDuplicateMenus(timelineMenuName, nukeMenuName):
  # Nuke menu
  nukeMenuItem = nukeMenuBar.menu(nukeMenuName)
  nukeMenuItem.setEnabled(True, True)
  nukeMenuAction = nukeMenuItem.action()
  setContext(nukeMenuAction, hiero.ui.kContextComp, True)
  # Hiero menu
  timelineAction = findMenuAction(timelineMenuName)
  setContext(timelineAction, hiero.ui.kContextTimeline, True)
  # Add the nuke menu next to the timeline menu
  menuBar().insertMenu(timelineAction, nukeMenuItem.action().menu())

# Reorders/rearranges menus for nuke studio. Sets the active context to determine
# when the actions should be visible.
def mergeMenus():
  # File menu
  fileMenu = findMenuAction("foundry.menu.file")
  # Set all the current file menu items to be timeline only
  for fileAction in fileMenu.menu().actions():
    # To avoid showing hidden recent files check first if the action already
    # has a context property set
    if fileAction.property(hiero.ui.kContextProperty) is None:
      setContext(fileAction, hiero.ui.kContextTimeline, False)
  # Set file menu to be visible in both timeline and comp modes, not recursive
  # so not setting menu items to be visible in both
  setContext(fileMenu, hiero.ui.kContextStudio, False)
  # Use hiero quit in both menus
  quitAction = findMenuAction('foundry.application.quit')
  setContext(quitAction, hiero.ui.kContextStudio, False)
  fileMenu.menu().insertSeparator(quitAction)
  # Add nuke items to the timeline file menu
  fileMenu.menu().insertSeparator(quitAction)
  insertNukeAction(nukeMenuBar.findItem("File/New Comp..."), fileMenu.menu(), before = 'foundry.application.quit', context = hiero.ui.kContextComp)
  insertNukeAction(nukeOpenItem, fileMenu.menu(), before = 'foundry.application.quit')
  # Add new menu for recent file as just adding the action doesn't work on OSX
  recentFilesNukeMenu = fileMenu.menu().addMenu("Open Recent Comp")
  fileMenu.menu().insertMenu(quitAction, recentFilesNukeMenu)
  openRecentCompItem = nukeMenuBar.findItem("File/Open Recent Comp")
  openRecentCompAction = openRecentCompItem.action()
  for recentFileAction in openRecentCompAction.menu().actions():
    recentFileAction.setEnabled(True)
    insertAction(recentFileAction, recentFilesNukeMenu)
    recentNukeActions.append(recentFileAction)
  # Add the rest of the nuke file menu items
  insertNukeAction(nukeCloseItem, fileMenu.menu(), before = 'foundry.application.quit')
  fileMenu.menu().insertSeparator(quitAction)
  insertNukeAction(nukeSaveItem, fileMenu.menu(), before = 'foundry.application.quit')
  insertAction(saveAndReRenderAction, fileMenu.menu(), before = 'foundry.application.quit', context = hiero.ui.kContextTimeline)
  insertNukeAction(nukeSaveAsItem, fileMenu.menu(), before = 'foundry.application.quit')
  insertNukeAction(nukeMenuBar.findItem("File/Save New Comp Version"), fileMenu.menu(), before = 'foundry.application.quit')
  fileMenu.menu().insertSeparator(quitAction)
  insertNukeAction(nukeMenuBar.findItem("File/Insert Comp Nodes..."), fileMenu.menu(), before = 'foundry.application.quit')
  insertNukeAction(nukeMenuBar.findItem("File/Export Comp Nodes..."), fileMenu.menu(), before = 'foundry.application.quit')
  insertNukeAction(nukeMenuBar.findItem("File/Comp Script Command..."), fileMenu.menu(), before = 'foundry.application.quit', context = hiero.ui.kContextComp)
  insertNukeAction(nukeMenuBar.findItem("File/Run Script..."), fileMenu.menu(), before = 'foundry.application.quit', context = hiero.ui.kContextComp)
  insertNukeAction(nukeMenuBar.findItem("File/Comp Info"), fileMenu.menu(), before = 'foundry.application.quit', context = hiero.ui.kContextComp)
  fileMenu.menu().insertSeparator(quitAction)
  insertNukeAction(nukeMenuBar.findItem("File/Clear"), fileMenu.menu(), before = 'foundry.application.quit', context = hiero.ui.kContextComp)
  fileMenu.menu().insertSeparator(quitAction)
  # TODO on OSX these shortcuts result in the items never being hidden
  # Disabling the shortcuts for now to ensure Run Script & Comp Info are visible only in comp views
  if sys.platform.startswith("darwin"):
    runScriptItem = nukeMenuBar.findItem("File/Run Script...")
    runScriptItem.action().setShortcut("")
    compInfoItem = nukeMenuBar.findItem("File/Comp Info")
    compInfoItem.action().setShortcut("")

  # Edit Menu
  initDuplicateMenus("foundry.menu.edit", "Edit")

  # Special case for the prefs action:
  # - On Mac it should appear in the application menu. Adding it to the timeline Edit
  # menu caused problems because in Qt 5.12 this causes it to be disabled when in a
  # comp context so it's in its own special preferences menu.
  # - On other platforms it should be in the Edit menu, add it to the comp edit menu as well
  # so it appears in both contexts
  if sys.platform.startswith("darwin"):
    prefsMenuAction = findMenuAction("foundry.menu.preferences")
    setContext(prefsMenuAction, hiero.ui.kContextStudio, True)
  else:
    preferencesAction = findMenuAction("foundry.application.preferences")
    setContext(preferencesAction, hiero.ui.kContextStudio, False)
    nukeEditItem = nukeMenuBar.menu("Edit")
    nukeEditItem.action().menu().addSeparator()
    insertMenuAction(preferencesAction, nukeEditItem.action().menu())

  # Workspace menu
  workspaceMenuItem = findMenuAction("foundry.menu.workspace")
  workspaceMenu = workspaceMenuItem.menu()
  setContext(workspaceMenuItem, hiero.ui.kContextStudio, False)
  # Add the some nuke actions
  workspaceMenu.addSeparator()
  nukeToggleFloatingItem = nukeMenuBar.findItem("Workspace/Toggle Hide Floating Viewers")
  insertNukeAction(nukeToggleFloatingItem, workspaceMenu, before = 'foundry.menu.navigation')
  insertNukeAction(nukeMenuBar.findItem("Workspace/Show Curve Editor"), workspaceMenu, before = 'foundry.menu.navigation')
  insertNukeAction(nukeMenuBar.findItem("Workspace/Close Tab"), workspaceMenu, after = 'foundry.menu.navigation')
  # Connect hiero floating viewers action to be triggered by nukes and the hide hiero toggle floating viewers and use nuke's
  heiroToggleViewersAction = findMenuAction("foundry.application.toggleFloatingViewers")
  nukeToggleFloatingItem.action().triggered.connect(heiroToggleViewersAction.trigger)
  hideAction(heiroToggleViewersAction)

  # Viewer Menu
  initDuplicateMenus("foundry.menu.viewer", "Viewer")

  # Render menu
  initDuplicateMenus("foundry.menu.render", "Render")

  # Cache menu
  initDuplicateMenus("foundry.menu.cache", "Cache")
  # Window menu
  windowMenuItem = findMenuAction("foundry.menu.window")
  windowMenu = windowMenuItem.menu()
  setContext(windowMenuItem, hiero.ui.kContextStudio, True)

  # Help menu
  helpMenuItem = findMenuAction("foundry.menu.help")
  helpMenu = helpMenuItem.menu()
  setContext(helpMenuItem, hiero.ui.kContextStudio, True)
  # Add nuke items to help menu
  nukeShortcutsItem = nukeMenuBar.findItem("Help/Comp Keyboard Shortcuts")
  insertNukeAction(nukeShortcutsItem, helpMenu, after = 'foundry.help.shortcuts', context = hiero.ui.kContextStudio)
  nukePlugInInstallerItem = nukeMenuBar.findItem("Help/Nuke Plug-ins")
  insertNukeAction(nukePlugInInstallerItem, helpMenu, context = hiero.ui.kContextStudio)

  # Init the menus that are only visible in the timeline context
  timelineOnlyMenus = ["foundry.menu.project",
                       "foundry.menu.clip",
                       "foundry.menu.sequence"]
  for menuName in timelineOnlyMenus:
    menuItem = findMenuAction(menuName)
    setContext(menuItem, hiero.ui.kContextTimeline, True)

  # Connect up the File and Edit menus to the aboutToShowMenu slot so that the
  # nuke menu actions are updated before these menus are shown.
  editMenu = findMenuAction("foundry.menu.edit")
  fileMenu.menu().aboutToShow.connect(aboutToShowMenu)
  editMenu.menu().aboutToShow.connect(aboutToShowMenu)

def hideAction(action):
  action.setVisible(False)
  action.setEnabled(False)
  setContext(action, hiero.ui.kContextNone, True)

def hideNukeMenus():
  for menu in list(nukeMenuBar.items()):
    menu.setVisible(False)
    menu.setEnabled(False, True) # True for recursive
    setContext(menu.action(), hiero.ui.kContextNone, True)

def appendNukeUserMenus():
  """ Get nuke user created menus and add them so they appear at the end of the menu bar
  """
  # Nuke Menus used to filter the list given by nuke.menu('Nuke').items()
  nukeMenusName = ('File', 'Edit', 'Workspace', 'Viewer', 'Render', 'Cache', 'Help' )
  # create list with User Menus
  nukeUserMenus = [ i for i in list(nuke.menu('Nuke').items()) if i.name() not in nukeMenusName ]

  # add User Menus to the end of MenuBar
  mainMenuBar = menuBar()
  for m in nukeUserMenus:
    nukeUserMenu = nukeMenuBar.menu(m.name())
    if nukeUserMenu:
      nukeUserMenuAction = nukeUserMenu.action()
      nukeUserMenu.setEnabled(True, True)
      setContext(nukeUserMenuAction, hiero.ui.kContextStudio, True)

      # Bug 43563 - User actions with and without menus can be added to the Nuke menu.
      # Both kinds need to be added to the NukeStudio menu.
      actionMenu = nukeUserMenuAction.menu()
      isStandaloneAction = actionMenu is None
      if isStandaloneAction:
        mainMenuBar.addAction( nukeUserMenuAction )
      else:
        mainMenuBar.addMenu( actionMenu )


# Sets the action's active context
def setContext(action, context, recursive):
  if action:
    # Special start value to indicate the item is hidden (nuke's hacky way to have multiple shortcuts for same menu action)
    if (action.text().startswith("@;")):
      action.setProperty(hiero.ui.kContextProperty, hiero.ui.kContextNone)
    else:
      action.setProperty(hiero.ui.kContextProperty, context)
    if recursive:
      subMenu = action.menu()
      if subMenu:
        for subAction in subMenu.actions():
          setContext(subAction, context, True)

def updateMenuActionVisibility(action, focusInNuke):
  """ Recursively set the visibility of menu actions based on their context,
  and whether keyboard focus is in a Nuke widget.
  """

  # Update the visibility of sub-menu items first. On Mac, when showing a menu
  # while all it's children are still hidden, it might not be made visible in the
  # system menu.
  subMenu = action.menu()
  if subMenu:
    for subAction in subMenu.actions():
      updateMenuActionVisibility(subAction, focusInNuke)

  context = action.property(hiero.ui.kContextProperty)
  if context == hiero.ui.kContextTimeline:
    action.setVisible(not focusInNuke)
  elif context == hiero.ui.kContextComp:
    action.setVisible(focusInNuke)
    action.setEnabled(focusInNuke)
  elif context == hiero.ui.kContextNone:
    action.setVisible(False)
  elif context == hiero.ui.kContextStudio:
    action.setVisible(True)
  else:
    action.setVisible(True)

def setMenuVisibility(focusInNuke):
  hieroMenuBar = menuBar()
  for menuAction in hieroMenuBar.actions():
    updateMenuActionVisibility(menuAction, focusInNuke)

  _switchContextShortcuts(focusInNuke)


def _switchContextShortcuts(focusInNuke):
  """Change some menus shortcuts so they don't clash"""
  # TODO Deal with clashing shortcuts here for now
  if focusInNuke:
    nukeOpenItem.action().setShortcut("Ctrl+O")
    nukeCloseItem.action().setShortcut("Ctrl+W")
    nukeSaveItem.action().setShortcut("Ctrl+S")
    nukeSaveAsItem.action().setShortcut("Ctrl+Shift+S")
    for idx, recentAction in enumerate(recentNukeActions):
      recentAction.setShortcut("Alt+Shift+" + str(idx + 1))
  else:
    nukeOpenItem.action().setShortcut("")
    nukeCloseItem.action().setShortcut("")
    nukeSaveItem.action().setShortcut("")
    nukeSaveAsItem.action().setShortcut("")
    for idx, recentAction in enumerate(recentNukeActions):
      recentAction.setShortcut("")


def nodeGraphExists():
  """ Returns True if a Node Graph (DAG) exists in the current workspace,
      False otherwise
  """
  mw = hiero.ui.mainWindow()
  windows = mw.findChildren( QtWidgets.QWidget, QtCore.QRegExp( 'DAG.\d' ) )
  return len(windows) > 0


def showViewer():
  """ Show Viewer Window of the first Viewer Node from nuke.allNodes("Viewer") """
  viewerNodes = nuke.allNodes("Viewer")
  if len(viewerNodes) > 0:
    nuke.show(viewerNodes[0])


## right click Open In context menu action and handler

class OpenInNodeGraphAction(QtWidgets.QAction):

  def __init__(self, studioEventHandler, fork):
    if fork:
      QtWidgets.QAction.__init__(self, "New Nuke Session", None)
    else:
      QtWidgets.QAction.__init__(self, "Node Graph", None)

    self.triggered.connect(self.doOpen)
    self.studioEventHandler = studioEventHandler
    hiero.core.events.registerInterest("kShowContextMenu/kTimeline", self.eventHandler)
    hiero.core.events.registerInterest("kShowContextMenu/kBin", self.eventHandler)
    self.fork = fork

  def doOpen(self):

    filePath = self.studioEventHandler.getNukeScriptPathFromItem( self.shotSelection[0] )

    if filePath:
      self.studioEventHandler.openDAG( filePath, self.fork )


  def eventHandler(self, event):
    if not hasattr(event.sender, 'selection'):
      # Something has gone wrong, we should only be here if raised
      # by the timeline view which will give a selection.
      return

    self.shotSelection = [item for item in event.sender.selection() if ( isinstance(item,hiero.core.TrackItem) or isinstance(item, hiero.core.BinItem) )]

    if len(self.shotSelection) != 1:
      return

    filePath = self.studioEventHandler.getNukeScriptPathFromItem( self.shotSelection[0] )

    if not filePath:
      return

    for a in event.menu.actions():
      if a.text().lower().strip() == "open in":
        hiero.ui.insertMenuAction( self, a.menu(), before = "foundry.project.openInViewer" )


class NukeStudioEventHandler:
  def __init__(self):
    # Listen for double click events, so we can open the DAG from double clicking in the timeline and bin view
    hiero.core.events.registerInterest((hiero.core.events.EventType.kDoubleClick, hiero.core.events.EventType.kBin), self.onDoubleClick)
    hiero.core.events.registerInterest((hiero.core.events.EventType.kDoubleClick, hiero.core.events.EventType.kTimeline), self.onDoubleClick)

    # Connect kContextChanged callback for automatically switch application menus.
    hiero.core.events.registerInterest(hiero.core.events.EventType.kContextChanged, self.onContextChanged)

    # Instantiate the action to get it to register itself.
    openInNewNukeAction = OpenInNodeGraphAction(self, False)
    openInNodeGraphAction = OpenInNodeGraphAction(self, True)

  def _getCurrentNukeScriptName(self):
    """ Try to get the current Nuke script name.  Returns an empty string if not set.
        This is a around nuke.scriptName() to handle the exception which gets raised if there is no current name. """
    try:
      return nuke.scriptName()
    except:
      return ""

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

  def _checkSaveCurrentNukeScript(self):
    """ Try to save the current script.  Returns False if the user selected Cancel, True otherwise. """

    result = True

    root = nuke.root()
    if root is not None and root.modified():
      fileName = os.path.basename( root.name() )

      button = QtWidgets.QMessageBox.question( hiero.ui.mainWindow(), "Nuke Comp Modified", "You have unsaved Nuke Comp changes to " + str(fileName) + ".  Would you like to save?",
                                               QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Save )
      if button == QtWidgets.QMessageBox.Save:
        try:
          nuke.scriptSave()
        except: # Cancelled
          result = False
      elif button == QtWidgets.QMessageBox.Cancel:
        result = False

    return result


  def onDoubleClick(self, event):

    # Double click event from bin or timeline views.  If the user has clicked an nk
    # clip, open it.

    try:
      # Find the clicked clip.  If a track item was clicked on, we can get its clip source,
      # otherwise it should be a bin item
      filePath = self.getNukeScriptPathFromItem( event.item )

      # When you double click on an nk clip, the following logic applies:
      # - If the script is already open, we just switch to its tab
      # - If the script is not open, we check if the current script has been modified, and ask the user if they want to save it.
      #   They have the option to cancel, in which case nothing happens.
      #   Otherwise the new script is opened and the DAG is shown

      # if the control modifier is down we fork off another instance
      fork = ( event.modifiers & QtCore.Qt.ControlModifier )

      if filePath:
        self.openDAG(filePath, fork)

    except Exception as e:
      print(traceback.format_exc())


  def openDAG(self, filePath, fork = False):
    """ Open a script in the DAG, or in a new Nuke process if fork is true.
        The caller should make sure the filePath is actually a valid Nuke script. """

    if fork:
      nuke.fork( filePath )
      return

    try:

      # When you double click on an nk clip, the following logic applies:
      # - If the script is already open, we just switch to its tab
      # - If the script is not open, we check if the current script has been modified, and ask the user if they want to save it.
      #   They have the option to cancel, in which case nothing happens.
      #   Otherwise the new script is opened and the DAG is shown

      lastScriptFile = self._getCurrentNukeScriptName()

      openInDag = True

      if lastScriptFile != filePath:  # If the current open script is not the same as the one we're trying to open
        if nuke.executing():
          popUpMessage = "Open Comp is executing\n(rendering, tracking, etc.)\n%s"%(filePath)
          button = QtWidgets.QMessageBox.warning( hiero.ui.mainWindow(), "Unable to close", popUpMessage )
          return

        if self._checkSaveCurrentNukeScript():
          try:
            nuke.scriptClear()
          except Exception as e:
            popUpMessage = "Could not close '%s'\n%s"%(filePath, e.what())
            button = QtWidgets.QMessageBox.warning( hiero.ui.mainWindow(), "Unable to close", popUpMessage )
            return

          nuke.scriptOpen(filePath)
        else:
          openInDag = False

      if openInDag:
        # only switch to Compositing workspace if the Node Graph is not
        # present in the current workspace
        if (hiero.ui.currentWorkspace() != "Compositing") and (not nodeGraphExists()):
          hiero.ui.setWorkspace("Compositing")

        # shows the DAG whether the script is already opened or not. The DAG is no longer shown when calling nuke.scriptOpen
        nuke.showDag(nuke.root())

        # force a Viewer Window to be shown (if a Viewer Node exists)
        # The Viewer Window will not be shown if the current workspace doesn't
        # have a placeholder for it. To prevent this, showViewer will check if
        # there is any ViewerNode in the nuke.root node and show it's Window
        showViewer()

    except Exception as e:
      # TODO: remove this catch-all
      pass


  def onContextChanged(self, event):
    focusInNuke = event.focusInNuke
    setMenuVisibility(focusInNuke)

    if focusInNuke:
      nukeUndoItem.setEnabled(nuke.Undo.undoSize() > 0, False)
      nukeRedoItem.setEnabled(nuke.Undo.redoSize() > 0, False)
    else:
      hieroUndoItem.setEnabled(hiero.core.undoSize() > 0)
      hieroRedoItem.setEnabled(hiero.core.redoSize() > 0)


runningInGui = QtCore.QCoreApplication.instance().inherits("QApplication")
if runningInGui:

  def setupMenus():
    # Hide all nuke menus
    hideNukeMenus()

    # Merge the nuke menus with the hiero/timeline menus
    mergeMenus()

    # append nuke user created menus to the end
    appendNukeUserMenus()

    # sets menu visibility according to the starting workspace
    isNukeWorkspace = currentWorkspace() == 'Compositing'
    setMenuVisibility( isNukeWorkspace )

  # gui setup has to occur after Hiero is fully initialized, otherwise we'll be accessing preferences before the preferences manager
  # is fully initialized. Only an issue for code in the hiero.ui or hiero.core modules directly, as they load before Hiero has
  # mucked with the modules to add the extra methods it exposes
  def setup():
    # have to make sure we're referencing the global variables
    global hieroState
    global addEffectHandler
    global eventHandler
    global frameServer
    # initialize our state management object
    hieroState = hiero_state.HieroState()

    # create our event handler object
    addEffectHandler = add_effect.AddEffectHandler(hieroState)

    # Create handler for double click and focus changed notifications.  Do this after setting up the menus.
    eventHandler = NukeStudioEventHandler()

  setupMenus()

  # initialize the gui for the hiero nuke bridge a bit later
  QtCore.QTimer.singleShot(0, setup)



#backwards compatibilty for frameserver methods
#frameserver methods have been moved to FnNsFrameServer
#adding these methods and globals here for backwards compatibility

frameServer = hiero.ui.nuke_bridge.FnNsFrameServer.frameServer
backgroundRenderObserver = hiero.ui.nuke_bridge.FnNsFrameServer.backgroundRenderObserver
renderProgressObserver = hiero.ui.nuke_bridge.FnNsFrameServer.renderProgressObserver
backgroundRenderer = hiero.ui.nuke_bridge.FnNsFrameServer.backgroundRenderer


from hiero.ui.nuke_bridge.FnNsFrameServer import (
  configureFrameServerFromCommandArgs,
  workerCount,
  startServer,
  stopServer,
  promptFrameServerKill,
  onFatalError,
  isServerRunning,
  renderFrames,
  renderScript,
  cancelFrames,
  setBackgroundRenderer)
