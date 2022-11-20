# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import hiero.core
from .Script import *
import os.path

_knobsToInitializeWithCreateNode = {
  "Viewer":set(["fps"])
}

class PythonScriptWriter(ScriptWriter):
  def __init__(self, autoConnectNodes=True, autoPosition=True):
    ScriptWriter.__init__(self)
    
    self._fileContents = ""
    self._lastNodeVariableName = ""
    self._lastVariableIndex = 0
    self._autoConnectNodes = autoConnectNodes
    self._variableNames = {}
    self._autoPosition = autoPosition

  def __repr__(self):
    # post process the script to add anything extra in
    self._postProcessNodes()
    
    # reset our output
    self._fileContents = ""
    
    # add a method at the top of the script to catch bad knob names
    self._fileContents += """# wrap set knob calls, so that if someone put in a bad knob name, it won't stop things\n
def setKnobValue(node, knobName, value, fromScript):
  try:
    if fromScript:
      node.knob(knobName).fromScript(value)
    else:
      node.knob(knobName).setValue(value)
  except:
    pass

"""
    
    # write out the nodes
    self._fileContents += "# Creating the nodes\n"
    for node in self._nodes:      
      self._serializingNode = node
      node.serialize(self)
      
    # write out all of their connections now
    if not self._autoConnectNodes:
      self._fileContents += "\n# Connecting the nodes\n"
      for node in self._nodes:      
        self._writeConnectingNodes(node)
        
    # autoplace, after connecting
    if self._autoPosition:
      self._fileContents += "\n# Autopositioning the nodes\n"
      for node in self._nodes:
        self._autoPositionNode(node)

    # get them all to execute now (which is unnecessary if you pass this to Nuke on the command line, using -x script.py)
    #self._fileContents += "root = nuke.root()\n"
    #self._fileContents += "start = root.knob(\"first_frame\").value()\n"
    #self._fileContents += "end = root.knob(\"last_frame\").value()\n"
    #self._fileContents += "nuke.executeMultiple([root], ((start, end, 1),))\n"

    return self._fileContents
  
  def _autoPositionNode(self, node):
    if node.type() != "Root":
      self._fileContents += "%s.autoplace()\n" % (self._variableNames[node])
  
  def _writeConnectingNodes(self, node):
    inputNodes = node.inputNodes()
    if len(inputNodes) < 1:
      return
    
    currentVariableName = self._variableNames[node]
    
    for (inputNumber, node) in inputNodes.items():
      self._fileContents += "%s.connectInput(%d, %s)\n" % (currentVariableName, inputNumber, self._variableNames[node])

    # throw in some white space, for good measure
    self._fileContents += "\n"
  
  ############################################################################################
  # Methods that allow this object to be sent to the serialize method of KnobFormatter objects
  ############################################################################################
  
  def beginSerializeNode(self, nodeType):
    
    isRootNode = (nodeType == "Root")
    if isRootNode:
      # don't need to create the root node, so we just serialize out the knobs
      variableName = "rootNode"
    else:
      # create a variable name
      variableName = "newNode" + str(self._lastVariableIndex)
    
      # increment our variable name counter
      self._lastVariableIndex += 1
    
    # store it, for this node
    self._variableNames[self._serializingNode] = variableName
    
    # keep track of it for setting the knob values
    self._lastNodeType = nodeType
    self._lastNodeVariableName = variableName
    self._nodeInitializerList = None
    self._knobCommands = ""
  
  def endSerializeNode(self):
    
    # we delayed writing everything out till now, so that we could collect knob's needed for the nodeInitializerList
    isRootNode = (self._lastNodeType == "Root")
    if isRootNode:      
      self._fileContents += self._lastNodeVariableName + " = nuke.root()\n"
    else:  
      # write the actual script portion now
      if self._nodeInitializerList != None:
        # there are some knobs that have to be set on node creation, or they don't work properly
        self._fileContents += "%s = nuke.createNode(\"%s\", \"%s\")\n" % (self._lastNodeVariableName, self._lastNodeType, self._nodeInitializerList)
      else:
        self._fileContents += "%s = nuke.createNode(\"%s\")\n" % (self._lastNodeVariableName, self._lastNodeType)
    
    # deselect it, if we're not autoconnecting, so that it doesn't auto connect to the next node created
    if not self._autoConnectNodes and (not isRootNode):
      self._fileContents += "%s.knob(\"selected\").setValue(False)\n" % (self._lastNodeVariableName)
      
    # add the knob setting commands
    self._fileContents += self._knobCommands
    
    # put a space between this node declaration and the next
    self._fileContents += "\n"
  
  def serializeKnob(self, knobType, knobValue):
    
    # when writing 
    if (knobType == "inputs") and (not self._autoConnectNodes):
      return
    
    # check if this is a special knob type
    if (self._lastNodeType in _knobsToInitializeWithCreateNode):
      if (knobType in _knobsToInitializeWithCreateNode[self._lastNodeType]):
        if self._nodeInitializerList != None:
          self._nodeInitializerList += " "
        else:
          self._nodeInitializerList = ""
        self._nodeInitializerList += "%s %s" % (knobType, knobValue)
        return
    
    if isinstance(knobValue, str):
      # assume that strings that start with quotes are already escaped and should be fed through as is
      # for everything else, escape quotes in the string and put quotes on either end
      if not knobValue.startswith('"'):
        knobValue= "\"" + knobValue.replace("\"", "\\\"") + "\""
        
      # if it's a string, do it through fromScript
      self._knobCommands += "setKnobValue(%s, \"%s\", %s, True)\n" % (self._lastNodeVariableName, knobType, knobValue)
    else:
      # otherwise, use setValue, so that we can use non-strings
      self._knobCommands += "setKnobValue(%s, \"%s\", %s, False)\n" % (self._lastNodeVariableName, knobType, str(knobValue))
      
  def serializeUserKnob(self, type, knobName, text, tooltip, value):
    pass
