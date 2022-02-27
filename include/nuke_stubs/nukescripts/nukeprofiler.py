import nuke
import socket
import datetime
import platform
from . import hardwareinfo


profileCategories = {
    "ProfileStore" : nuke.PROFILE_STORE,
    "ProfileValidate" : nuke.PROFILE_VALIDATE,
    "ProfileRequest": nuke.PROFILE_REQUEST,
    "ProfileEngine" : nuke.PROFILE_ENGINE,
    }

class NukeProfiler:
  def __init__(self):
    self._pathToFile = nuke.performanceProfileFilename()
    self._profileDesc = None
    self._file = None
    self._indent = 0

  def setPathToFile(self, filename):
    self._pathToFile = filename

  def indentString(self):
    return "  " * self._indent

  def OpenTag(self, tagName, optionsDict = {}, closeTag = False):
    xmlString = self.indentString() + "<" + tagName + ">\n"
    if closeTag:
      xmlString += "\n"
    self._indent += 1
    for dictKey, dictValue in optionsDict.items():
      xmlString +=  self.indentString() + "<" + dictKey + ">" + str(dictValue) + "</" + dictKey + ">\n"
    if closeTag:
      self._indent -= 1
      xmlString += self.indentString() + "</" + tagName + ">\n"
    return xmlString

  def CloseTag(self, tagName):
    self._indent -= 1
    closeTagString = self.indentString() + "</" + tagName + ">\n"
    return closeTagString

  def WriteDictInner(self, dictToWrite):
    xmlString = ""
    for dictKey, dictValue in dictToWrite.items():
      xmlString += self.indentString() + "<" + dictKey + ">" + str(dictValue) + "</" + dictKey + ">\n"
    return xmlString

  def NodeProfile(self, nukeNode, maxEngineVal):
    nodeTag = "Node"
    if nukeNode.Class() == "Group":
      # Use a different tag for Group nodes, which contain combined performance statistics for all the nodes within the group.
      # The internal nodes are also output separately so including group nodes as well means these nodes get counted twice.
      # Using a different tag makes it clear that these should be treated differently to other nodes when parsing the xml
      # for analysis or display.
      nodeTag = "GroupNode"
    nodeInfoDict = { "Name" : nukeNode.fullName(), "Class" : nukeNode.Class() }
    # Add the file path if the node is a Reader or Writer
    if nukeNode.Class() == "Read" or nukeNode.Class() == "Write":
      nodeInfoDict["File"] = nukeNode["file"].value()
    xmlString = self.OpenTag(nodeTag,  nodeInfoDict)
    for catName, catVal in profileCategories.items():
      xmlString += self.OpenTag(catName)
      if catName == "ProfileEngine":
        info = nukeNode.performanceInfo(catVal).copy()
        if maxEngineVal > 0:
          perfVal = float(info["timeTakenWall"]) / float(maxEngineVal)
        else:
          perfVal = -1.0
        info.update({ "ProfileEngineRelativeToMax" : perfVal })
        xmlString += self.WriteDictInner(info)
      else:
        xmlString += self.WriteDictInner(nukeNode.performanceInfo(catVal))
      xmlString += self.CloseTag(catName)
    xmlString += self.CloseTag(nodeTag)
    return xmlString

  def initProfileDesc(self):
    commandLineString = ""
    for i in nuke.rawArgs:
      commandLineString += i + " "
    self._profileDesc = {
      "ScriptName" : nuke.root().name(),
      "NumThreads" : nuke.env["threads"],
      "TimeStored" : str(datetime.datetime.now().replace(microsecond = 0)),
      "CommandLine" : commandLineString
   }

  def writeXMLInfo(self):
    self._file.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
    self._file.write("<?xml-stylesheet type=\"text/xsl\" href=\"testStylesheet.xsl\"?>\n")

  def resetTimersAndStartProfile(self):
    nuke.resetPerformanceTimers()
    self.initProfileDesc()
    self._file = open(self._pathToFile, "w")
    self.writeXMLInfo()
    self.writeProfileDesc()

  def writeProfileDesc(self):
    self._file.write(self.OpenTag("PerformanceProfile", self._profileDesc))
    self._file.write(self.OpenTag("MachineInfo"))
    hardwareinfo.PrintMachineInfoToFile(self._file, self._indent)
    self._file.write(self.CloseTag("MachineInfo"))

  def addFrameProfileAndResetTimers(self):
    self._file.write(self.OpenTag("Frame", { "Time" : nuke.frame() }))
    self._file.write(self.OpenTag("MaxPerformance"))
    # Store max engine value for calculating relative performance:
    maxInfo = nuke.maxPerformanceInfo()
    maxEngineVal = maxInfo["timeTakenWall"]["value"]
    for key, value in maxInfo.items():
      self._file.write(self.OpenTag(key))
      self._file.write(self.WriteDictInner(value))
      self._file.write(self.CloseTag(key))
    self._file.write(self.CloseTag("MaxPerformance"))
    # Fill in node profile
    for n in nuke.allNodes(recurseGroups = True):
      self._file.write(self.NodeProfile(n, maxEngineVal));
    self._file.write(self.CloseTag("Frame"))
    # Reset performance timers after writing the profile for this frame:
    nuke.resetPerformanceTimers()

  def endProfile(self):
    # If in a GUI session and nothing has been rendered out to a
    # file, the profile file will not have been opened yet, so
    # check that the file exists before trying to close it:
    if self._file != None:
      self._file.write(self.CloseTag("PerformanceProfile"))
      self._file.close()







