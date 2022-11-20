# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

from ui import *
from _fnpython import mainWindow, menuBar, activeView, activeSequence, registeredActions, registerAction, findRegisteredAction, findRegisteredActions, currentWorkspace, setWorkspace, saveWorkspace, resetCurrentWorkspace, getTimelineEditor
import threading
import os
from PySide2 import (QtCore, QtGui, QtWidgets)
import _nuke

# the following are Hiero/Studio only things, check if the exports feature is enabled
import hiero.core
if 'exports' in hiero.core.env['Features']:
  from .FnExporterBaseUI import TaskUIBase, RenderTaskUIBase
  from .FnProcessorUI import ProcessorUIBase
  from .FnExportUIRegistry import TaskUIRegistry, taskUIRegistry
  from .FnExporterBaseUI import InvalidOutputResolutionMessage

from .FnVersionWidget import VersionWidget

from foundry.ui import openFileBrowser

from . import FnViewerMethods

# Constants used to determine menu actions' visibilty
kContextProperty = "ActiveContext"
kContextNone = 0
kContextStudio = 1
kContextTimeline = 2
kContextComp = 3

# Menus
def _addMenuActionR( path, action, menu, before = None ):
  # Find first path element in menu
  name = path[0]
  for a in menu.actions():
    if name == a.objectName() or name == a.text():
      if len( path ) <= 1:
        if before != None:
          for b in a.menu().actions():
            if before == b.objectName() or before == b.text():
              a.menu().insertAction( b, action )
              return True
        else:
          a.menu().addAction( action )
        return True
      else:
        _addMenuActionR( path[1:], action, a.menu() )
        return True
  # We didn't find the menu
  return False


def addMenuAction( path, action, before = None ):
  """
  Add a QAction to the main menubar. The 'path' parameter specifies the menu to which to add the action as a '/'-separated string.
  The path may contain either internal action names or display names. e.g. 'View/Transform', or (better) 'foundry.menu.view/foundry.view.transform'."
  The optional 'before' parameter specifies the name of an item the action should be inserted before. If this is not specified, the action is appended to the menu.
  """
  return _addMenuActionR( path.split( "/" ), action, menuBar(), before )

def createMenuAction(name, method, icon = None, path = None):
  """
  Creates a menu action (QAction) for use in context menus or Main menubar.
  The 'name' parameter specifies the title of the action.
  @param: name - the title of the menu action
  @param: method - the Python method which this action triggers
  @param: icon (optional) - provides an icon for the action. This can be an absolute path ('/var/tmp/myIcon.png'), or relative path ('icons:myIcon.png')
  @param: path (optional) - the path to the menu action. The action objects name will be set to this value
  """

  action = QtWidgets.QAction(name, None)
  if icon:
    action.setIcon(QtGui.QIcon(icon))

  if path:
    action.setObjectName(path)

  action.triggered.connect( method )
  return action

def insertMenuAction( action, menu, before = None, after = None ):
  """
  Insert a QAction into the given QMenu. If strings 'before' or 'after' are specified, the action is inserted before or after the action with that name.
  If no such action is found or 'before/after' are not given, the action is appended to the menu.
  """
  insert = False
  for a in menu.actions():
    if insert:
      menu.insertAction( a, action )
      return
    if before != None:
      if before == a.objectName() or before == a.text():
        menu.insertAction( a, action )
        return
    if after != None:
      if after == a.objectName() or after == a.text():
        insert = True
  menu.addAction( action )


def _findMenuActionR( name, menu ):
  for a in menu.actions():
    if name == a.objectName() or name == a.text():
      return a
    if a.menu() != None:
      result = _findMenuActionR( name, a.menu() )
      if result != None:
        return result
  return None


def findMenuAction( name ):
  """
    Find a QAction in the main menubar. The 'name' parameter specifies the name of the action.
    The name may be either an internal action name or a display name. e.g. 'Cut', or (better) 'foundry.application.cut'."
    """
  return _findMenuActionR( name, menuBar() )


def trackNameValidator ():
  namepatternrx = QtCore.QRegExp("[a-z A-Z 0-9 . _ -]*")
  nameval = QtGui.QRegExpValidator(namepatternrx)
  return nameval

# Panels
_panels = dict()

def registerPanel( id, command ):
  _panels[id] = command

def unregisterPanel( id, command ):
  del _panels[id]

def restorePanel( id ):
  try:
    return _panels[id]()
  except:
    log.debug( "Can't restore panel '" + str(id) + "' because it hasn't been registered." )
    return None


def getProjectRootInteractive(project):
  """ Try to get a valid root path from the project.  If the existing exportRootDirectory()
      is not set or doesn't exist, the user will be prompted to select one.  If no path
      is selected, returns None. """
  projectRoot = project.exportRootDirectory()

  # If the project root is not set or the directory doesn't exist, ask the user to select a path
  if not projectRoot or not hiero.core.util.filesystem.exists(projectRoot):
    fileList = openFileBrowser(caption="Please select a valid path for the Export Root", pattern="*/", mode=2, initialPath="/")
    if (fileList != None and len(fileList) > 0):
      projectRoot = fileList[0]
      project.setUseCustomExportDirectory(True)
      project.setCustomExportDirectory(projectRoot)
    else:
      projectRoot = None

  return projectRoot


from . import guides

viewer_guides = [
  guides.SimpleGuide("Title Safe", 1, 1, 1, 0.1, guides.kGuideMasked),
  guides.SimpleGuide("Action Safe", 1, 1, 1, 0.05, guides.kGuideMasked),
  guides.SimpleGuide("Format", 1, 0, 0, 0, guides.kGuideSequence, crosshairs = False),
]

viewer_masks = [
  guides.MaskGuide("Square", 1.0),
  guides.MaskGuide("4:3", 4.0/3.0),
  guides.MaskGuide("16:9", 16.0/9.0),
  guides.MaskGuide("14:9", 14.0/9.0),
  guides.MaskGuide("1.66:1", 1.66),
  guides.MaskGuide("1.85:1", 1.85),
  guides.MaskGuide("2.35:1", 2.35),
]

# Python Menus and Actions
from . import nuke_bridge
from . import RenameTimelineShots
from . import CopyCuts
from . import TagsMenu
from . import BuildExternalMediaTrack
from . import SendToNuke
from . import FnReExportAction
from . import ScanForVersions
from . import LocalisationMenu
from . import FnPosterFrameUI
