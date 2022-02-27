# Copyright (c) 2016 The Foundry Visionmongers Ltd.  All Rights Reserved.

import os.path

import nuke
import nukescripts

import re
from PySide2 import QtWidgets, QtGui, QtCore

kCommandField = 'Command:'
last_cmd = ''


def script_command(default_cmd):
    global last_cmd
    p = nuke.Panel("Nuke")
    if (default_cmd != None and len(default_cmd) != 0):
        use_cmd = default_cmd
    else:
        use_cmd = last_cmd
    p.addScriptCommand(kCommandField, use_cmd)
    p.addButton("Cancel")
    p.addButton("OK")
    result = p.show()
    if result == 1:
      last_cmd = p.value(kCommandField)
      p.execute(kCommandField)


def findMaxVersionForFileName(filename):
  """Helper function for finding the max version of a paticular
  script in it's current directory.
  Note that a file in the current directory will count towards the
  current version set if the string before the v number for that file
  is the same as the string before the v numebr of the current version."""

  # Get the maximum version number based in the current files on disk
  (basePath, fileNameCurrent) = os.path.split(filename)
  (prefixCurrent, vCurrent) =  nukescripts.version_get(fileNameCurrent, "v")
  # Set maxV to the current version + 1
  maxV = int(vCurrent) + 1

  # Get the base name for the current file version.
  # i.e. the bit of the filename before the version number.
  baseNameRegex = "(.*)" + str(prefixCurrent)
  baseMatch = re.match(baseNameRegex, fileNameCurrent, re.IGNORECASE)

  if not baseMatch:
    return maxV

  baseNameCurrent = baseMatch.group(1)

  # Iterate the files in the current directory
  for fileName in os.listdir(basePath):
    # get the base name of each file.
    match = re.match(baseNameRegex, fileName, re.IGNORECASE)
    if not match:
      continue

    baseNameFile = match.group(1)

    # Check whether the base name is the same as the current file
    if baseNameFile == baseNameCurrent:
      # Compare the v number and update maxV if needed.
      (prefix, version) = nukescripts.version_get(fileName, "v")
      if int(version) > maxV:
        maxV = int(version) + 1

  return maxV


class VersionHelper(object):
  """Helper class for storing the new version information"""
  """Intended to be created per rootname."""
  def __init__(self, rootname):
    (prefix, v) =  nukescripts.version_get(rootname, "v")
    self._rootname = rootname
    self._prefix = prefix
    self._currentV = int(v)
    self._maxV = findMaxVersionForFileName(rootname)


  def hasVersion(self):
    return self._currentV is not None

  def nextVersion(self):
    return self._currentV + 1

  def maxVersion(self):
    return self._maxV

  def currentVersionString(self):
    return self._rootname

  def nextVersionString(self):
    return self.versionString(self.nextVersion())

  def maxVersionString(self):
    return self.versionString(self.maxVersion())

  def versionString(self, version):
    return nukescripts.version_set(self._rootname, self._prefix, self._currentV, version)
#End VersionHelper


class VersionConflictDialog(QtWidgets.QDialog):
  """Dialog which gives the user options for resolving version conflicts"""
  def __init__(self,versionHelper,parent=None):
    super(VersionConflictDialog, self).__init__(parent)

    self._newPath = None
    self._newVersion = None

    self._eButtonIds = {
      "overwrite": 0,
      "saveAsMax": 1,
      "saveAsVersion": 2,
    }

    self._versionHelper = versionHelper

    self.setWindowTitle("Version Conflict")
    self.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )
    self.setMinimumWidth(450)

    layout = QtWidgets.QVBoxLayout()
    layout.setSpacing(0)

    filename = versionHelper.nextVersionString()

    text = QtWidgets.QLabel("Unable to save script. Version:\n%s\nalready exists. \n\nWould you like to:" % filename)
    layout.addWidget(text)

    self._buttonGroup = QtWidgets.QButtonGroup(self)

    overwriteButton = QtWidgets.QRadioButton("Overwrite existing version")
    self._buttonGroup.addButton(overwriteButton)
    self._buttonGroup.setId(overwriteButton, self._eButtonIds["overwrite"])
    overwriteButton.setChecked(True)

    saveAsmaxVersionButton = QtWidgets.QRadioButton("Save as max version (%s)" % versionHelper._maxV)
    self._buttonGroup.addButton(saveAsmaxVersionButton)
    self._buttonGroup.setId(saveAsmaxVersionButton, self._eButtonIds["saveAsMax"])

    saveAsVersionButton = QtWidgets.QRadioButton("Save as version: ")
    self._buttonGroup.addButton(saveAsVersionButton)
    self._buttonGroup.setId(saveAsVersionButton, self._eButtonIds["saveAsVersion"])

    self._saveAsVersionSpin = QtWidgets.QSpinBox()
    self._saveAsVersionSpin.setValue(versionHelper._maxV)
    self._saveAsVersionSpin.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
    self._saveAsVersionSpin.setFixedWidth(30)
    self._saveAsVersionSpin.setContentsMargins(0,0,0,0)

    # Negative versions are not allowed, so set min valid version to 1
    versionValidator = QtGui.QIntValidator()
    versionValidator.setBottom(1)
    self._saveAsVersionSpin.lineEdit().setValidator(versionValidator)

    saveAsVerionLayout = QtWidgets.QHBoxLayout()
    saveAsVerionLayout.setSpacing(0)
    saveAsVerionLayout.setContentsMargins(0,0,0,0)
    saveAsVerionLayout.setAlignment(QtCore.Qt.AlignLeft)
    saveAsVerionLayout.addWidget(saveAsVersionButton)
    saveAsVerionLayout.addWidget(self._saveAsVersionSpin)

    layout.addWidget(overwriteButton)
    layout.addWidget(saveAsmaxVersionButton)
    layout.addLayout(saveAsVerionLayout)

    # Standard buttons for Add/Cancel
    buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
    buttonbox.accepted.connect(self.accept)
    buttonbox.rejected.connect(self.reject)
    layout.addWidget(buttonbox)

    self.setLayout(layout)

  def showDialog(self):
    result = self.exec_()

    if result:
      buttonId = self._buttonGroup.checkedId()

      if(buttonId < 0 ):
        return None

      #Get the correct path for that button ID
      if buttonId is self._eButtonIds["overwrite"]:
        self._newPath = self._versionHelper.nextVersionString()
        self._newVersion = self._versionHelper.nextVersion()
      elif buttonId is self._eButtonIds["saveAsMax"]:
        self._newPath = self._versionHelper.maxVersionString()
        self._newVersion = self._versionHelper.maxVersion()
      elif buttonId is self._eButtonIds["saveAsVersion"]:
        self._newVersion  = self._saveAsVersionSpin.value()
        self._newPath = self._versionHelper.versionString(self._newVersion )

    return result

  def getNewFilePath(self):
    # Get the checked button id from the button group
    return self._newPath

  def getNewVersionNumber(self):
    return self._newVersion
#End VersionDialog


def set_fileknob_version(knob, version):
  """Sets version of the filename knob to the passed in version.
     Throws with ValueError if fileKnob has no version."""
  currentPath = knob.value()
  if currentPath:
    (prefix, v) = nukescripts.version_get(currentPath, "v")
    newPath = nukescripts.version_set(currentPath, prefix, int(v), version)
    knob.setValue(newPath)


def timeline_write_version_set(version):
  """Sets the version number in the file path of the 'timeline' write node"""
  kTimelineWriteNodeKnobName = "timeline_write_node"

  timelineWriteNodeKnob = nuke.root().knob(kTimelineWriteNodeKnobName)
  if timelineWriteNodeKnob is not None:
    timelineWriteNodeName = timelineWriteNodeKnob.getText()
    writeNode = nuke.toNode(timelineWriteNodeName)
    if writeNode is not None:
      # Set file knob
      fileKnob = writeNode['file']
      set_fileknob_version(fileKnob, version)

      # Set proxy knob
      proxyKnob = writeNode['proxy']
      set_fileknob_version(proxyKnob, version)


def script_version_up():
  """ Increments the versioning in the script name and the path of the timeline
  write nodes, then saves the new version. """
  # Set up the version helper
  root_name = nuke.toNode("root").name()

  try:
    versionHelper = VersionHelper(root_name)
  except ValueError as e:
    nuke.message("Unable to save new comp version:\n%s" % str(e))
    return

  newFileName = versionHelper.nextVersionString()
  newVersion = versionHelper.nextVersion()

  # If the next version number already exists we need to ask the user how to proceed
  newVersionExists = os.path.exists( newFileName )
  if newVersionExists:
    versionDialog = VersionConflictDialog(versionHelper)
    cancelVersionUp = not versionDialog.showDialog()
    if cancelVersionUp:
      return
    else:
      newFileName = versionDialog.getNewFilePath()
      newVersion = versionDialog.getNewVersionNumber()

  # Get the Studio write Node and version up before saving the script
  try:
    timeline_write_version_set(newVersion)
  except Exception as e:
    shouldContinue = nuke.ask("Unable to set Write node version:\n%s\nDo you want to continue saving new comp version?" % str(e))
    if not shouldContinue:
      return

  #Make the new directory if needed
  dirName = os.path.dirname( newFileName )
  if not os.path.exists( dirName ):
      os.makedirs( dirName )

  #Save the script and add to the bin
  nuke.scriptSaveAs(newFileName)
  if nuke.env['studio']:
    from hiero.ui.nuke_bridge.nukestudio import addNewScriptVersionToBin
    addNewScriptVersionToBin(root_name, newFileName)


def script_and_write_nodes_version_up():
  # Just calls script_version_up
  script_version_up()


def get_script_data():
  activechans = nuke.Root.channels()
  totchan = len(activechans)

  root = nuke.toNode("root")
  rez = root.knob("proxy").value()

  numnodes = len(nuke.allNodes())

  chaninuse = totchan
  chanleft = 1023-totchan
  memusage = nuke.cacheUsage()/1024/1024
  output = "Script : "+root.name()+"\n"
  output = output+"Total nodes: "+str(numnodes)+"\n"
  if rez:
    output = output+"\nResolution : --PROXY--\n"
  else:
    output = output+"\nResolution : **FULL RES**\n"
  output += "\nElements:\n"+nukescripts.get_reads("long")

  output += "\nChannels in use: "+str(totchan)+"\n"
  output += "Channels left: "+str(chanleft)+"\n"
  output += "\nCache Usage: "+str(memusage)+" mb\n"
  output += "\nChannel Data :\n"

  layers = nuke.Root.layers()
  for i in layers:
    output += "\n"+i.name()+"\n"
    channels = i.channels()
    for j in channels:
      if j in activechans:
        output += "\t"+j+"\n"

  return output


def script_data():
  nuke.display("nukescripts.get_script_data()", nuke.root())


def script_directory():
  return nuke.script_directory()
