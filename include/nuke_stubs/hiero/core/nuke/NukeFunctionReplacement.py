"""This module defines new behavior (methods) for the Nuke Python API:
 nuke.scriptNew, nuke.scriptClose and nuke.scriptExit
 nuke.restoreWindowLayout and nuke.saveWindowLayout"""

import nuke
import hiero
from hiero.core.deprecated import deprecated
import subprocess
from PySide2 import (QtCore, QtWidgets)
import os

def scriptExitReplacementFunc(*args, **kwargs):
  """Exit the Application if 'forceExit' is True, otherwise 'nuke.scriptSaveAndClear' will be called
  @param forceExit: Optional parameter. Forces the Application to close.
  @return: None."""
  print("scriptExitReplacementFunc")
  forceExit = forceExit = kwargs.get("forceExit", False) 
  if forceExit:
    hiero.core.quit(0)
  else:
    shouldExit = nuke.scriptSaveAndClear()

    # check if running on Nuke Studio. If not scripExit should have the same
    # behavior as Nuke8, exiting after prompting the user if he wants to save any modification
    runningInNukeStudio = nuke.env['studio']
    if shouldExit and not runningInNukeStudio:
      hiero.core.quit(0)


# Replace Nuke's script* methods, preserving the original docs and function names
scriptExitReplacementFunc.__doc = nuke.scriptExit.__doc__
scriptExitReplacementFunc.__name__ = nuke.scriptExit.__name__
nuke.scriptExit = scriptExitReplacementFunc 

nuke.scriptClose = nuke.scriptSaveAndClear


if nuke.env['studio']:
  # replace nuke.scriptOpen only for nuke studio.
  # nuke.scriptOpen needs to behave in the same way
  # but when opening a new nk script, if there is no
  # need to fork a new instance we show the DAG if it
  # is in the current workspace or we switch to Compositing
  # workspace. This follow the same logic as when opening
  # a FX comp from the timeline.

  def _nodeGraphExists():
    """ Returns True if a Node Graph (DAG) exists in the current workspace,
        False otherwise
    """
    mw = hiero.ui.mainWindow()
    windows = mw.findChildren( QtWidgets.QWidget, QtCore.QRegExp( 'DAG.\d' ) )
    return len(windows) > 0


  def _showViewer():
    """ Show Viewer Window of the first Viewer Node from nuke.allNodes('Viewer') """
    viewerNodes = nuke.allNodes('Viewer')
    if len(viewerNodes) > 0:
      nuke.show(viewerNodes[0])


  def scriptOpenReplacementFunc( filePath ):
    """ Method to replace the nuke.scriptOpen in nuke studio.
        This method will use the orginal nuke.scripOpen but it checks 
        if a new instance of nuke will be created. If not the DAG will 
        be shown if it exists in the current workspace or we switch to
        the Compositing workspace"""

    root = nuke.root()
    isSavedScript = False
    try:
      # an exception will be raise if the current script doesn't
      # have a name, meaning that is an unsaved script
      isSavedScript = os.path.exists( nuke.scriptName() )
    except:
      pass

    processWillBeFork = root is not None and (root.modified() or isSavedScript) and len(root.nodes()) > 0

    try:
      nukeScriptOpenOldMethod(filePath)
    except nuke.CancelledError:
      # catch nuke.CancelledError in the case when Cancel was selected
      # so we don't need to change workspace or show the DAG
      return
    except:
      # Other exceptions may be raised (for example openning a
      # .nkple script without running in PLE raises a RuntimeError)
      # and they need to be handle in Python.cpp::doPython
      raise

    if not processWillBeFork:
      if (hiero.ui.currentWorkspace() != "Compositing") and (not _nodeGraphExists()):
        hiero.ui.setWorkspace("Compositing")
      nuke.showDag( root )
      _showViewer()


  scriptOpenReplacementFunc.__doc__ = nuke.scriptOpen.__doc__
  scriptOpenReplacementFunc.__name__ = nuke.scriptOpen.__name__

  nukeScriptOpenOldMethod = nuke.scriptOpen
  nuke.scriptOpen = scriptOpenReplacementFunc



def _getWorkspaceActions( returnSaveActions ):
  """ Returns a list of actions corresponding to restore/save workspace
  If returnSaveActions is False a list with the restore workspace 
  action will be returned, otherwise it will be a list with save 
  workspace actions."""
  
  # import findMenuAction here. The hiero.core module is not fully initialized
  # and an exception was being raised when importing the findMenuAction method
  from hiero.ui import findMenuAction
  workspaceMenuAction = findMenuAction('foundry.menu.workspace')
  workspaceMenu = workspaceMenuAction.menu()
  workspaceActions = workspaceMenu.actions()

  workspaceActions = [ a for a in workspaceActions if a.objectName().startswith('foundry.workspace.') ]
  if returnSaveActions:
    workspaceActions = [ a for a in workspaceActions if a.objectName().startswith('foundry.workspace.save.') ]
  else:
    workspaceActions = [ a for a in workspaceActions if not a.objectName().startswith('foundry.workspace.save.') ]

  return workspaceActions


def _triggerWorkspaceAction( actionIndex, saveAction ):
  """ Triggers the action (Restore workspace or Save workspace)
  corresponding to actionsIndex."""

  # subtract 1 to a transform in a 0 based index
  actionIndex = actionIndex - 1

  # get the workspace actions (restore or save) by the order
  # that they are in the workspace menu. In this way we can
  # trigger the action corresponding to actionIndex
  workspaceActions = _getWorkspaceActions( returnSaveActions = saveAction )

  if actionIndex >= 0 and actionIndex < len(workspaceActions):
    workspaceActions[ actionIndex ].trigger()


def restoreWorkspaceFunc(workspaceIndex):
  """ Method to replace the nuke.restoreWindowLayout. 
  It receives an integer [ 1 , number of available workspaces ]
  and restore the workspace corresponding with the input parameter."""
  
  _triggerWorkspaceAction( workspaceIndex , saveAction = False )


def saveWorkspaceFunc(workspaceIndex = 1):
  """ Method to replace the nuke.saveWindowLayout.
  It receives an interger [ 1 , number of available workspaces ]
  and saves the current layout with the name of the workspace name corresponding 
  to the input parameter."""

  _triggerWorkspaceAction( workspaceIndex , saveAction = True )
  

restoreWorkspaceFunc.__doc__ = nuke.restoreWindowLayout.__doc__
restoreWorkspaceFunc.__name__ = nuke.restoreWindowLayout.__name__
nuke.restoreWindowLayout = deprecated( restoreWorkspaceFunc, funcName = "nuke.restoreWindowLayout" , msg = """This method is deprecated. The Restore action in the Workspace Menu corresponding to the input argument will be triggered.\nhiero.ui.setWorkspace(name) should be called with the desired workspace name.""" ) 


saveWorkspaceFunc.__doc__ = nuke.saveWindowLayout.__doc__
saveWorkspaceFunc.__name__ = nuke.saveWindowLayout.__name__
nuke.saveWindowLayout = deprecated( saveWorkspaceFunc, funcName = "nuke.saveWindowLayout" , msg = """This method is deprecared. The Save action in the Workspace Menu corresponding to the input argument will be triggered.\nhiero.ui.saveWorkspace(name) should be called with the new workspace name.""" )
