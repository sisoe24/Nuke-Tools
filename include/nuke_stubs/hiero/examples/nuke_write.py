# An example of creating a nuke (\*.nk) script and using Nuke to render it

'''
This script shows how to:
  
* Create a nuke script writer
* Create and add a Nuke Read node, some modifier nodes, and a Write node to the script writer
* Write the script out
* Call Nuke to execute it (and render the write node)
* Ingest the rendered media back into Hiero

'''

import os.path
import sys, tempfile
from PySide2 import QtCore
from hiero.core import newProject
from hiero.core import MediaSource
from hiero.core import Clip
from hiero.core import BinItem
import hiero.core.nuke as nuke
from hiero.ui import *

def findResourcePath():

  hieroExecutablePath = QtCore.QCoreApplication.applicationDirPath()
  resourcesPath = str(os.path.abspath(os.path.join(hieroExecutablePath, "Documentation", "PythonDevGuide", "Hiero", "Resources")))

  # OS X paths are a bit different...
  if sys.platform.startswith("darwin")  :
    hieroExecutablePath = os.path.join(hieroExecutablePath, '..', '..', '..')
    resourcesPath = str(os.path.abspath(os.path.join(hieroExecutablePath, "Resources", "PythonDevGuide", "Hiero", "Resources")))

  return resourcesPath

def createClip():
  # find the path to the resources that ship with Hiero
  resourcesPath = findResourcePath()
  
  # create a new project
  myProject = newProject()

  # attach the bins to the project
  clipsBin = myProject.clipsBin()
  
  # create the clip now
  source = MediaSource(os.path.join(resourcesPath, "purple.######.dpx"))
  clip = Clip(source)
  clipsBin.addItem(BinItem(clip))

  return clip

def ingestNukeOutput(mediaPath):
  myProject = hiero.core.projects()[-1]
  
  # attach the bins to the project
  clipsBin = myProject.clipsBin()
  
  # create the clip now
  source = MediaSource(mediaPath)
  clip = Clip(source)
  clipsBin.addItem(BinItem(clip))
  
  # play the clip in the bin now
  currentViewer().setSequence(clip, 0)
  currentViewer().play()
  
def clipSourceRange(clip):
  try:
    fileInfos = clip.mediaSource().fileinfos()  
    return fileInfos[0].startFrame(), fileInfos[0].endFrame()
  except:
    print("couldn't get frame range for clip source")
    return (0, 100)


(file, path) = tempfile.mkstemp(prefix="hiero_")

# create a clip
clip = createClip()

# create a script writer
nukeScriptWriter = nuke.ScriptWriter()

# let the clip add itself, and a metadata node, to the script writer's list of nodes
clip.addToNukeScript(nukeScriptWriter)

# add a blur node
blurNode = nuke.Node("Blur")

# set some values on the blur node
blurNode.setKnob("size", 8)

# add it to the script writer's node list
nukeScriptWriter.addNode(blurNode)

# now make the output blue with a grade; set the gain knob value to something appropriate
# notice that since this is a complex knob (a 4 component colour value)
# we have to specially TCL escape it with the {} brackets, otherwise
# Nuke will not read the script properly
gainKnobValue = "{0.4540588856 2.65821147 3.25 1}"

# note that you can send knob values into the Node initializer as well,
# meaning we can create the Grade, set it's gain value (which is actually
# the 'white' knob in Nuke), and add it to the nuke script writer all in
# one line
nukeScriptWriter.addNode(nuke.Node("Grade", white=gainKnobValue))

# create a write node
writeNodeOutput = path + ".mov"
writeNode = nuke.WriteNode(writeNodeOutput)

# lock the write node's frame range to the same as the input, so that it comes back in that way
# you could have alternatively created a root node as the first node and set the frame range there
first, last = clipSourceRange(clip)
writeNode.setKnob("first", first)
writeNode.setKnob("last", last)
writeNode.setKnob("use_limit", 1)

# add the write node to the script
nukeScriptWriter.addNode(writeNode)

# write the script to disk
scriptPath = path + ".nk"
nukeScriptWriter.writeToDisk(scriptPath)

if not os.path.exists(scriptPath):
  
  print("Failed to write %s" % scriptPath)
  
else:
  print("Successfully wrote %s. Executing now..." % scriptPath)
  sys.stdout.flush()

  # get hiero to call nuke to execute the script
  logFileName = path + ".log"
  process = nuke.executeNukeScript(scriptPath, open( logFileName, 'w' ))
  
  # executeNukeScript returns a subprocess.POpen object, which we need to poll for completion
  def poll():
    returnCode = process.poll()
    
    # if the return code hasn't been set, Nuke is still running
    if returnCode == None:
      
      print("Still executing...")
      sys.stdout.flush()
      
      # fire a timer to poll again
      QtCore.QTimer.singleShot(100, poll)
    else:
      
      print("execution finished")

      # check if the path exists now
      if os.path.exists(writeNodeOutput):
        print("%s successfully rendered (from %s)" % (writeNodeOutput, scriptPath))
      else:
        print("%s failed to render" % writeNodeOutput)
      
      # ingest it back into the project now
      ingestNukeOutput(writeNodeOutput)

  # start polling
  poll()
  
