# Copyright (c) 2010 The Foundry Visionmongers Ltd.  All Rights Reserved.

_gDropDataCallbacks = []

def addDropDataCallback(callback):
  """Add a function to the list of callbacks. This function will called whenever data is dropped onto the DAG. Override it to perform other actions.
  If you handle the drop, return True, otherwise return None."""
  _gDropDataCallbacks.append(callback)

def dropData(mimeType, text):
  """Handle data drops by invoking the list of callback functions until one has
     handled the event"""
  for callback in reversed(_gDropDataCallbacks):
    if callback(mimeType, text) == True:
      return True
  return None

