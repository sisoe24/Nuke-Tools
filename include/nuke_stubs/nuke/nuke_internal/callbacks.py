# callbacks.py
#
# Callbacks from Nuke to user-defined Python.
# Nuke actually calls "nuke.onCreate()" but users will normally use
# the default versions of these functions and use "nuke.addOnCreate()"
# to add to the list of callbacks that the default calls.

import types
import nuke_internal as nuke


def _addCallback(_dict, call, args, kwargs, nodeClass, node=None):
  if not callable(call):
    raise ValueError("call must be a callable")
  if type(args) != tuple:
    args = (args,)
  if type(kwargs) != dict:
    raise ValueError("kwargs must be a dictionary")
  if nodeClass in _dict:
    list = _dict[nodeClass]
    # make it appear only once in list
    try:
      list.remove((call,args,kwargs,node))
    except:
      pass
    list.append((call,args,kwargs,node))
  else:
    _dict[nodeClass] = [(call,args,kwargs,node)]

def _removeCallback(_dict, call, args, kwargs, nodeClass, node=None):
  if type(args) != tuple:
    args = (args,)
  if nodeClass in _dict:
    list = _dict[nodeClass]
    try:
      list.remove((call,args,kwargs,node))
    except:
      pass

def _doCallbacks(_dict, node=None):
  list = _dict.get(nuke.thisClass())
  node = nuke.thisNode()
  if list:
    for f in list:
      if f[3] == None or f[3] is node:
        f[0](*f[1],**f[2])
  list = _dict.get('*')
  if list:
    for f in list:
      if f[3] == None or f[3] is node:
        f[0](*f[1],**f[2])

onUserCreates={}
def addOnUserCreate(call, args=(), kwargs={}, nodeClass='*'):
  """Add code to execute when user creates a node"""
  _addCallback(onUserCreates, call, args, kwargs, nodeClass)
def removeOnUserCreate(call, args=(), kwargs={}, nodeClass='*'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(onUserCreates, call, args, kwargs, nodeClass)
def onUserCreate():
  _doCallbacks(onUserCreates)
  if not len(onUserCreates): nuke.tcl("OnCreate")

onCreates={}
def addOnCreate(call, args=(), kwargs={}, nodeClass='*'):
  """Add code to execute when a node is created or undeleted"""
  _addCallback(onCreates, call, args, kwargs, nodeClass)
def removeOnCreate(call, args=(), kwargs={}, nodeClass='*'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(onCreates, call, args, kwargs, nodeClass)
def onCreate():
  _doCallbacks(onCreates)

onScriptLoads={}
def addOnScriptLoad(call, args=(), kwargs={}, nodeClass='Root'):
  """Add code to execute when a script is loaded"""
  _addCallback(onScriptLoads, call, args, kwargs, nodeClass)
def removeOnScriptLoad(call, args=(), kwargs={}, nodeClass='Root'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(onScriptLoads, call, args, kwargs, nodeClass)
def onScriptLoad():
  _doCallbacks(onScriptLoads)

onScriptSaves={}
def addOnScriptSave(call, args=(), kwargs={}, nodeClass='Root'):
  """Add code to execute before a script is saved"""
  _addCallback(onScriptSaves, call, args, kwargs, nodeClass)
def removeOnScriptSave(call, args=(), kwargs={}, nodeClass='Root'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(onScriptSaves, call, args, kwargs, nodeClass)
def onScriptSave():
  _doCallbacks(onScriptSaves)

onScriptCloses={}
def addOnScriptClose(call, args=(), kwargs={}, nodeClass='Root'):
  """Add code to execute before a script is closed"""
  _addCallback(onScriptCloses, call, args, kwargs, nodeClass)
def removeOnScriptClose(call, args=(), kwargs={}, nodeClass='Root'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(onScriptCloses, call, args, kwargs, nodeClass)
def onScriptClose():
  _doCallbacks(onScriptCloses)

onDestroys={}
def addOnDestroy(call, args=(), kwargs={}, nodeClass='*'):
  """Add code to execute when a node is destroyed"""
  _addCallback(onDestroys, call, args, kwargs, nodeClass)
def removeOnDestroy(call, args=(), kwargs={}, nodeClass='*'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(onDestroys, call, args, kwargs, nodeClass)
def onDestroy():
  _doCallbacks(onDestroys)

knobChangeds={}
def addKnobChanged(call, args=(), kwargs={}, nodeClass='*', node=None):
  """Add code to execute when the user changes a knob
  The knob is availble in nuke.thisKnob() and the node in nuke.thisNode().
  This is also called with dummy knobs when the control panel is opened
  or when the inputs to the node changes. The purpose is to update other
  knobs in the control panel. Use addUpdateUI() for changes that
  should happen even when the panel is closed."""
  _addCallback(knobChangeds, call, args, kwargs, nodeClass, node)
def removeKnobChanged(call, args=(), kwargs={}, nodeClass='*', node=None):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(knobChangeds, call, args, kwargs, nodeClass, node)
def knobChanged():
  _doCallbacks(knobChangeds)

updateUIs={}
def addUpdateUI(call, args=(), kwargs={}, nodeClass='*'):
  """Add code to execute on every node when things change. This is done
  during idle, you cannot rely on it being done before it starts updating
  the viewer"""
  _addCallback(updateUIs, call, args, kwargs, nodeClass)
def removeUpdateUI(call, args=(), kwargs={}, nodeClass='*'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(updateUIs, call, args, kwargs, nodeClass)
def updateUI():
  _doCallbacks(updateUIs)

# autolabel is somewhat different due to it returning a string
autolabels={}
def addAutolabel(call, args=(), kwargs={}, nodeClass='*'):
  """Add code to execute on every node to produce the text to draw on it
  in the DAG. Any value other than None is converted to a string and used
  as the text. None indicates that previously-added functions should
  be tried"""
  _addCallback(autolabels, call, args, kwargs, nodeClass)
def removeAutolabel(call, args=(), kwargs={}, nodeClass='*'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(autolabels, call, args, kwargs, nodeClass)
def autolabel():
  list = autolabels.get(nuke.thisClass())
  if list:
    for f in list[::-1]:
      s = f[0](*f[1],**f[2])
      if s != None: return s
  list = autolabels.get('*')
  if list:
    for f in list[::-1]:
      s = f[0](*f[1],**f[2])
      if s != None: return s

# Normal rendering callbacks
beforeRenders={}
def addBeforeRender(call, args=(), kwargs={}, nodeClass='Write'):
  """Add code to execute before starting any renders"""
  _addCallback(beforeRenders, call, args, kwargs, nodeClass)
def removeBeforeRender(call, args=(), kwargs={}, nodeClass='Write'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(beforeRenders, call, args, kwargs, nodeClass)
def beforeRender():
  _doCallbacks(beforeRenders)

beforeFrameRenders={}
def addBeforeFrameRender(call, args=(), kwargs={}, nodeClass='Write'):
  """Add code to execute before each frame of a render"""
  _addCallback(beforeFrameRenders, call, args, kwargs, nodeClass)
def removeBeforeFrameRender(call, args=(), kwargs={}, nodeClass='Write'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(beforeFrameRenders, call, args, kwargs, nodeClass)
def beforeFrameRender():
  _doCallbacks(beforeFrameRenders)

afterFrameRenders={}
def addAfterFrameRender(call, args=(), kwargs={}, nodeClass='Write'):
  """Add code to execute after each frame of a render"""
  _addCallback(afterFrameRenders, call, args, kwargs, nodeClass)
def removeAfterFrameRender(call, args=(), kwargs={}, nodeClass='Write'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(afterFrameRenders, call, args, kwargs, nodeClass)
def afterFrameRender():
  _doCallbacks(afterFrameRenders)

afterRenders={}
def addAfterRender(call, args=(), kwargs={}, nodeClass='Write'):
  """Add code to execute after any renders"""
  _addCallback(afterRenders, call, args, kwargs, nodeClass)
def removeAfterRender(call, args=(), kwargs={}, nodeClass='Write'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(afterRenders, call, args, kwargs, nodeClass)
def afterRender():
  _doCallbacks(afterRenders)

renderProgresses={}
def addRenderProgress(call, args=(), kwargs={}, nodeClass='Write'):
  """Add code to execute when the progress bar updates during any renders"""
  _addCallback(renderProgresses, call, args, kwargs, nodeClass)
def removeRenderProgress(call, args=(), kwargs={}, nodeClass='Write'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(renderProgresses, call, args, kwargs, nodeClass)
def renderProgress():
  _doCallbacks(renderProgresses)

# Callbacks for internal use only
_beforeRecordings={}
def addBeforeRecording(call, args=(), kwargs={}, nodeClass='Viewer'):
  """Add code to execute before viewer recording"""
  _addCallback(_beforeRecordings, call, args, kwargs, nodeClass)
def removeBeforeRecording(call, args=(), kwargs={}, nodeClass='Viewer'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(_beforeRecordings, call, args, kwargs, nodeClass)
def beforeRecording():
  _doCallbacks(_beforeRecordings)

_afterRecordings={}
def addAfterRecording(call, args=(), kwargs={}, nodeClass='Viewer'):
  """Add code to execute after viewer recording"""
  _addCallback(_afterRecordings, call, args, kwargs, nodeClass)
def removeAfterRecording(call, args=(), kwargs={}, nodeClass='Viewer'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(_afterRecordings, call, args, kwargs, nodeClass)
def afterRecording():
  _doCallbacks(_afterRecordings)

_beforeReplays={}
def addBeforeReplay(call, args=(), kwargs={}, nodeClass='Viewer'):
  """Add code to execute before viewer replay"""
  _addCallback(_beforeReplays, call, args, kwargs, nodeClass)
def removeBeforeReplay(call, args=(), kwargs={}, nodeClass='Viewer'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(_beforeReplays, call, args, kwargs, nodeClass)
def beforeReplay():
  _doCallbacks(_beforeReplays)

_afterReplays={}
def addAfterReplay(call, args=(), kwargs={}, nodeClass='Viewer'):
  """Add code to execute after viewer replay"""
  _addCallback(_afterReplays, call, args, kwargs, nodeClass)
def removeAfterReplay(call, args=(), kwargs={}, nodeClass='Viewer'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(_afterReplays, call, args, kwargs, nodeClass)
def afterReplay():
  _doCallbacks(_afterReplays)

# Special functions to perform background callbacks as these have no node as
# context.
def _addBackgroundCallback(list, call, args, kwargs):
  if not callable(call):
    raise ValueError("call must be a callable")
  if type(args) != tuple:
    args = (args,)
  if type(kwargs) != dict:
    raise ValueError("kwargs must be a dictionary")
  # make it appear only once in list
  try:
    list.remove((call,args,kwargs))
  except:
    pass
  list.append((call,args,kwargs))

def _removeBackgroundCallback(list, call, args, kwargs):
  if type(args) != tuple:
    args = (args,)
  try:
    list.remove((call,args,kwargs))
  except:
    pass

def _doBackgroundCallbacks(list, context):
  for f in list:
    f[0](context, *f[1],**f[2])

# Background rendering callbacks
beforeBackgroundRenders=[]
def addBeforeBackgroundRender(call, args=(), kwargs={}):
  """Add code to execute before starting any background renders.
  The call must be in the form of:
  def foo(context):
    pass

  The context object that will be passed in is a dictionary containing the following elements:
  id => The identifier for the task that's about to begin

  Please be aware that the current Nuke context will not make sense in the callback (e.g. nuke.thisNode will return a random node).
  """
  _addBackgroundCallback(beforeBackgroundRenders, call, args, kwargs)
def removeBeforeBackgroundRender(call, args=(), kwargs={}):
  """Remove a previously-added callback with the same arguments."""
  _removeBackgroundCallback(beforeBackgroundRenders, call, args, kwargs)
def beforeBackgroundRender(context):
  _doBackgroundCallbacks(beforeBackgroundRenders, context)

# There is no logical place for this to be called at the moment, so don't expose it.
#def addBeforeBackgroundFrameRender(call, args=(), kwargs={}):
#  """Add code to execute before each frame of a background render"""
#  _addBackgroundCallback(beforeBackgroundFrameRenders, call, args, kwargs)
#def removeBeforeBackgroundFrameRender(call, args=(), kwargs={}):
#  """Remove a previously-added callback with the same arguments."""
#  _removeBackgroundCallback(beforeBackgroundFrameRenders, call, args, kwargs)
#def beforeBackgroundFrameRender():
#  _doBackgroundCallbacks(beforeBackgroundFrameRenders)

afterBackgroundFrameRenders=[]
def addAfterBackgroundFrameRender(call, args=(), kwargs={}):
  """Add code to execute after each frame of a background render.
  The call must be in the form of:
  def foo(context):
    pass

  The context object that will be passed in is a dictionary containing the following elements:
  id => The identifier for the task that's making progress
  frame => the current frame number being rendered
  numFrames => the total number of frames that is being rendered
  frameProgress => the number of frames rendered so far.

  Please be aware that the current Nuke context will not make sense in the callback (e.g. nuke.thisNode will return a random node).
  """
  _addBackgroundCallback(afterBackgroundFrameRenders, call, args, kwargs)
def removeAfterBackgroundFrameRender(call, args=(), kwargs={}):
  """Remove a previously-added callback with the same arguments."""
  _removeBackgroundCallback(afterBackgroundFrameRenders, call, args, kwargs)
def afterBackgroundFrameRender(context):
  _doBackgroundCallbacks(afterBackgroundFrameRenders, context)

afterBackgroundRenders=[]
def addAfterBackgroundRender(call, args=(), kwargs={}):
  """Add code to execute after any background renders.
  The call must be in the form of:
  def foo(context):
    pass

  The context object that will be passed in is a dictionary containing the following elements:
  id => The identifier for the task that's ended

  Please be aware that the current Nuke context will not make sense in the callback (e.g. nuke.thisNode will return a random node).
  """
  _addBackgroundCallback(afterBackgroundRenders, call, args, kwargs)
def removeAfterBackgroundRender(call, args=(), kwargs={}):
  """Remove a previously-added callback with the same arguments."""
  _removeBackgroundCallback(afterBackgroundRenders, call, args, kwargs)
def afterBackgroundRender(context):
  _doBackgroundCallbacks(afterBackgroundRenders, context)

# filenameFilter is somewhat different due to it returning a string
filenameFilters={}
def addFilenameFilter(call, args=(), kwargs={}, nodeClass='*'):
  """Add a function to modify filenames before Nuke passes them to
  the operating system. The first argument to the function is the
  filename, and it should return the new filename. None is the same as
  returning the string unchanged. All added functions are called
  in backwards order."""
  _addCallback(filenameFilters, call, args, kwargs, nodeClass)
def removeFilenameFilter(call, args=(), kwargs={}, nodeClass='*'):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(filenameFilters, call, args, kwargs, nodeClass)

def filenameFilter(filename):
  global filenameFilters
  if filenameFilters:
    # Run the filename through registered callbacks, starting with class-specific 
    # ones. There are issues with calling thisClass() here so only do it if a 
    # class-specific callback has been registered
    allNodesFilter = filenameFilters.get('*', [])
    if len(filenameFilters) > 1 or not allNodesFilter:
      classFilter = filenameFilters.get(nuke.thisClass(), [])
      for f in classFilter[::-1]:
        s = f[0](filename,*f[1],**f[2])
        if s != None: filename = s
    for f in allNodesFilter[::-1]:
      s = f[0](filename,*f[1],**f[2])
      if s != None: filename = s
  else:
    # For back-compatibility allow user to define a filenameFix() function:
    import __main__
    if 'filenameFix' in __main__.__dict__:
      return __main__.__dict__['filenameFix'](filename)
    # For even further back-compatibility let them define a tcl filename_fix function:
    return nuke.tcl("filename_fix",filename)
  return filename

validateFilenames={}
def addValidateFilename(call, args=(), kwargs={}, nodeClass='Write'):
  """Add a function to validate a filename in Write nodes. The first argument
  is the filename and it should return a Boolean as to whether the filename is valid
  or not. If a callback is provided, it will control whether the Render button of Write nodes
  and the Execute button of WriteGeo nodes is enabled or not."""
  _addCallback(validateFilenames, call, args, kwargs, nodeClass)
def removeFilenameValidate(call, args=(), kwargs={}, nodeClass='Write'):
  """Remove a previously-added callback."""
  _removeCallback(validateFilenames, call, args, kwargs, nodeClass)
def validateFilename(filename):
  import __main__
  list = validateFilenames.get(nuke.thisClass())
  valid = True

  if list:
    for f in list:
      b = f[0](filename)
      if b == False: valid = False
  list = validateFilenames.get('*')
  if list:
    for f in list:
      b = f[0](filename)
      if b == False: valid = False
  return valid


def _doAutoSaveCallbacks( filters, filename ):
  import __main__
  list = filters.get( 'Root' )
  if list:
    for f in list:
      s = f[0](filename)
      filename = s

  return filename

autoSaveFilters={}
def addAutoSaveFilter(filter):
  """addAutoSaveFilter(filter) -> None

  Add a function to modify the autosave filename before Nuke saves the current script on an autosave timeout.

  Look at rollingAutoSave.py in the nukescripts directory for an example of using the auto save filters.

  @param filter: A filter function.  The first argument to the filter is the current autosave filename.
  The filter should return the filename to save the autosave to."""
  _addCallback(autoSaveFilters, filter, (), {}, 'Root')

def removeAutoSaveFilter(filter):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(autoSaveFilters, call, (), {}, 'Root')

def autoSaveFilter(filename):
  """Internal function.  Use addAutoSaveFilter to add a callback"""
  return _doAutoSaveCallbacks( autoSaveFilters, filename )


autoSaveRestoreFilters={}
def addAutoSaveRestoreFilter(filter):
  """addAutoSaveRestoreFilter(filter) -> None

  Add a function to modify the autosave restore file before Nuke attempts to restores the autosave file.

  Look at rollingAutoSave.py in the nukescripts directory for an example of using the auto save filters.

  @param filter: A filter function.  The first argument to the filter is the current autosave filename.
  This function should return the filename to load autosave from or it should return None if the autosave file should be ignored."""
  _addCallback(autoSaveRestoreFilters, filter, (), {}, 'Root')

def removeAutoSaveRestoreFilter(filter):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(autoSaveRestoreFilters, filter, (), {}, 'Root')

def autoSaveRestoreFilter(filename):
  """Internal function.  Use addAutoSaveRestoreFilter to add a callback"""
  return _doAutoSaveCallbacks( autoSaveRestoreFilters, filename )

autoSaveDeleteFilters={}
def addAutoSaveDeleteFilter(filter):
  """addAutoSaveDeleteFilter(filter) -> None

  Add a function to modify the autosave filename before Nuke attempts delete the autosave file.

  Look at rollingAutoSave.py in the nukescripts directory for an example of using the auto save filters.

  @param filter: A filter function.  The first argument to the filter is the current autosave filename.
  This function should return the filename to delete or return None if no file should be deleted."""
  _addCallback(autoSaveDeleteFilters, filter, (), {}, 'Root')

def removeAutoSaveDeleteFilter(filter):
  """Remove a previously-added callback with the same arguments."""
  _removeCallback(autoSaveDeleteFilters, filter, (), {}, 'Root')

def autoSaveDeleteFilter(filename):
  """Internal function.  Use addAutoSaveDeleteFilter to add a callback"""
  return _doAutoSaveCallbacks( autoSaveDeleteFilters, filename )

