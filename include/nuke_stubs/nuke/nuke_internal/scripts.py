"""This module define the scriptSaveAndClear method for Nuke API.
nuke.scriptSaveAndClear will call nuke.scriptSave() if any changes were made and then calls nuke.scriptClear()
"""

import nuke_internal as nuke

def scriptSaveAndClear(filename=None, ignoreUnsavedChanges=False):
  """ scriptSaveAndClear(filename=None, ignoreUnsavedChanges=False) -> None
  Calls nuke.scriptSave and nuke.scriptClear
  @param filename: Save to this file name without changing the script name in the
   project.
  @param ignoreUnsavedChanges: Optional. If set to True scripSave will be called,
   ignoring any unsaved changes
  @return: True when sucessful. False if the user cancels the operation. In this
   case nuke.scripClear will not be called
   """

  root = nuke.Root()
  if not ignoreUnsavedChanges and root is not None and root.modified() and len(root.nodes()) > 0:

    runScriptSave = False

    if filename is None:
      scriptName = ''
      try:
        scriptName = nuke.scriptName()
      except RuntimeError:
        scriptName = 'untitled'
      try:
        runScriptSave = nuke.askWithCancel( "Save changes to " + scriptName + " before closing?" )
      except nuke.CancelledError:
        return False
    else:
      runScriptSave = True

    if runScriptSave:
      try:
        nuke.scriptSave( filename )
      except RuntimeError:
        return False

  nuke.scriptClear()
  return True
