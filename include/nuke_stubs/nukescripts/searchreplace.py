# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke
import re

def __NodeHasKnobWithName(node, name):
  try:
    node[name]
  except NameError:
    return False
  else:
    return True

def __NodeHasFileKnob(node):
  return __NodeHasKnobWithName(node, 'file')

def __NodeHasProxyKnob(node):
  return __NodeHasKnobWithName(node, 'proxy')

def __ReplaceKnobValue(searchstr, replacestr, knob):
  v = knob.value()
  if v:
    repl = re.sub(searchstr, replacestr, v)
    knob.setValue(repl)

def search_replace():
  """ Search/Replace in Reads and Writes. """
  fileKnobNodes = [i for i in nuke.selectedNodes() if __NodeHasFileKnob(i)]
  proxyKnobNodes = [i for i in nuke.selectedNodes() if __NodeHasProxyKnob(i)]
  if not fileKnobNodes and not proxyKnobNodes: raise ValueError("No nodes selected")

  p = nuke.Panel("Search/Replace in Reads and Writes")
  p.addSingleLineInput("Search for:", "rgbea")
  p.addSingleLineInput("Replace with:", "rgbea")
  success = p.show()
  if success == 1:
    searchstr = p.value("Search for:")
    replacestr = p.value("Replace with:")

    for i in fileKnobNodes: __ReplaceKnobValue(searchstr, replacestr, i['file'])
    for i in proxyKnobNodes: __ReplaceKnobValue(searchstr, replacestr, i['proxy'])

