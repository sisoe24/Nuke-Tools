# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import time
import hiero.core

from . FnExportKeywords import kFileBaseKeyword, kFileHeadKeyword, kFilePathKeyword, KeywordTooltips
from . FnEffectHelpers import ensureEffectsNodesCreated

class BinProcessor(hiero.core.ProcessorBase):

  def __init__(self, preset, submission=None, synchronous=False):
    """Initialize"""
    hiero.core.ProcessorBase.__init__(self, preset, submission, synchronous)

    self._exportTemplate = None

    self.setPreset(preset)


  def preset (self):
    return self._preset


  def setPreset ( self, preset ):
    self._preset = preset

    oldTemplate = self._exportTemplate
    self._exportTemplate = hiero.core.ExportStructure2()
    self._exportTemplate.restore(self._preset._properties["exportTemplate"])
    if self._preset._properties["exportRoot"] != "None":
      self._exportTemplate.setExportRootPath(self._preset._properties["exportRoot"])


  def _buildBinPath (self, project, binItem, root):
    # Walk the bin structure and build list of bin names
    binPath = []
    while binItem is not None:
      if binItem == project.clipsBin():
        binItem = None
      elif root and binItem == root:
        binItem = None
      else:
        binPath.append(binItem.name())
        binItem = binItem.parentBin()
    # Concatenate bin names to form binpath
    return "/".join(reversed(binPath))

  def startProcessing(self, exportItems, preview=False):
    hiero.core.log.info( "BinProcessor::startProcessing(" + str(exportItems) + ")" )

    tasks = []

    localtime = time.localtime(time.time())

    path = self._exportTemplate.exportRootPath()
    versionIndex = self._preset.properties()["versionIndex"]
    versionPadding = self._preset.properties()["versionPadding"]
    version = "v%s" % format(versionIndex, "0%id" % int(versionPadding))

    startFrame = None
    if self._preset.properties()["startFrameSource"] == "Custom":
      startFrame = self._preset.properties()["startFrameIndex"]

    # Keep a list of resolved export paths, so we can detect duplicates
    exportPaths = []

    self._submission.setFormatDescription( self._preset.name() )

    # Get the clips to export
    anythingAdded = False
    for item in exportItems:
      if item.clip() and (item.clip().mediaSource().isMediaPresent() or not self.skipOffline()):

        anythingAdded = True
        taskGroup = hiero.core.TaskGroup()
        taskGroup.setTaskDescription( item.clip().name() )
        self._submission.addChild(taskGroup)

        for (exportPath, preset) in self._exportTemplate.flatten():

          # TODO Unlike the other processors, this is not copying the objects. Copied
          # clips don't belong to a project and this has caused some problems. Also,
          # the shot and timeline processors copy the sequence being exported, but
          # not the clips being referenced by it although these are still accessed
          # in the export. While this is technically not thread safe, clips
          # very rarely change and it hasn't caused any issues. A  better solution
          # should be found though.
          clip = item.clip()

          project = clip.project()
          binItem = item.binItem().parentBin()
          rootSelection = item.root().parentBin() if item.root() is not None else project.clipsBin()

          # Concatenate bin names to form binpath
          binPath = self._buildBinPath(project, binItem, rootSelection)
          fullBinPath = self._buildBinPath(project, binItem, project.clipsBin())

          # Create a resolver from the preset (specific to this type of processor)
          resolver = self._preset.createResolver()

          # Populate "bin path"
          resolver.addResolver("{binpath}", "Path within the bin, up to the selected BinItem. If no BinItem selected, path up to project", binPath)
          resolver.addResolver("{fullbinpath}", "Path within the bin, up to the project", fullBinPath)

          # Create export task seed
          taskData = hiero.core.TaskData(preset, clip, path, exportPath, version, self._exportTemplate,
            project=project, retime=True, startFrame=startFrame, resolver=resolver, submission=self._submission, skipOffline=self.skipOffline())
          # Create task
          task = hiero.core.taskRegistry.createTaskFromPreset(preset, taskData)

          # Add task to export queue
          if task:
            # Give the task an oppertunity to modify the original (not the copy) sequence
            if not task.error() and not preview:
              task.updateItem(clip, localtime)
            tasks.append(task)
            taskGroup.addChild( task )
            hiero.core.log.info( "Added to Queue " + task.name() )
            # If resolved path has already been encountered, mark as duplicate and cancel
            if task.resolvedExportPath() in exportPaths:
              task.setDuplicate()
            else:
              exportPaths.append(task.resolvedExportPath())

          if preview:
            # If previewing only generate tasks for the first item, otherwise it
            # can slow down the UI
            if tasks:
              break

      elif item.clip() and not item.clip().mediaSource().isMediaPresent():
        hiero.core.log.debug( "%s is offline. Ignoring." % str(item.clip().name()) )
      else:
        hiero.core.log.debug( "%s is not a Clip. Ignoring." % str(item) )

    # If processor is flagged as Synchronous, flag tasks too
    if not preview:
      if self._synchronous:
        self._submission.setSynchronous()

      if self._submission.children():

        # Detect any duplicates
        self.processTaskPreQueue()

        self._submission.addToQueue()
    return tasks


class BinProcessorPreset(hiero.core.ProcessorPreset):
  def __init__(self, name, properties):
    hiero.core.ProcessorPreset.__init__(self, BinProcessor, name)

    # setup defaults
    self.properties()["versionIndex"] = 1
    self.properties()["versionPadding"] = 2
    self.properties()["exportTemplate"] = ( )
    self.properties()["exportRoot"] = "{projectroot}"
    self.properties()["startFrameIndex"] = 1001
    self.properties()["startFrameSource"] = "Source"
    self.properties().update(properties)

    # This remaps the project root if os path remapping has been set up in the preferences
    self.properties()["exportRoot"] = hiero.core.remapPath (self.properties()["exportRoot"])

  def addCustomResolveEntries(self, resolver):
    """addDefaultResolveEntries(self, resolver)
    Create resolve entries for default resolve tokens shared by all task types.
    @param resolver : ResolveTable object"""

    resolver.addResolver("{filename}", "Filename of the media being processed", lambda keyword, task: task.fileName())
    resolver.addResolver(kFileBaseKeyword, KeywordTooltips[kFileBaseKeyword], lambda keyword, task: task.filebase())
    resolver.addResolver(kFileHeadKeyword, KeywordTooltips[kFileHeadKeyword], lambda keyword, task: task.filehead())
    resolver.addResolver(kFilePathKeyword, KeywordTooltips[kFilePathKeyword], lambda keyword, task: task.filepath())
    resolver.addResolver("{filepadding}", "Source Filename padding for formatting frame indices", lambda keyword, task: task.filepadding())
    resolver.addResolver("{fileext}", "Filename extension part of the media being processed", lambda keyword, task: task.fileext())
    resolver.addResolver("{clip}", "Name of the clip used in the shot being processed", lambda keyword, task: task.clipName())
    resolver.addResolver("{binpath}", "Path within the bin, up to the selected BinItem. If no BinItem selected, path up to project", "")
    resolver.addResolver("{fullbinpath}", "Path within the bin, up to the project", "")


hiero.core.taskRegistry.registerProcessor(BinProcessorPreset, BinProcessor)
