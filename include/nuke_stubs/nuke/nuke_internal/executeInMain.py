# Functions for parallel threads to run stuff that can only be
# in the main Nuke thread. Formerly in nukescripts.utils

import traceback
import threading
import types
import _nuke

def executeInMainThreadWithResult( call, args = (), kwargs = {}):
  """ Execute the callable 'call' with optional arguments 'args' and named arguments 'kwargs' in
      Nuke's main thread and wait for the result to become available. """
  if type(args) != tuple:
    args = (args,)

  resultEvent = threading.Event()
  id = _nuke.RunInMainThread.request(call, args, kwargs, resultEvent )
  resultEvent.wait()
  try:
    r = _nuke.RunInMainThread.result(id)
  except:
    traceback.print_exc()
    r = None

  return r

def executeInMainThread(call, args = (), kwargs = {}):
  """ Execute the callable 'call' with optional arguments 'args' and named
  arguments 'kwargs' i n Nuke's main thread and return immediately. """
  if type(args) != tuple:
    args = (args,)
  _nuke.RunInMainThread.request(call, args, kwargs)



