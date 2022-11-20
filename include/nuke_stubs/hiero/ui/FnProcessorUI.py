import itertools
import ui
import os
import errno
import traceback
import hiero.core
import hiero.core.FnExporterBase as FnExporterBase
from hiero.ui.FnElidedLabel import ElidedLabel
from PySide2 import (QtCore, QtWidgets)
from ui import IProcessorUI
from hiero.core.FnCompSourceInfo import CompSourceInfo
from hiero.core.util import filesystem


def isCompItemMissingRenders(compItem):
  """ Check if renders for a comp item are missing or out of date. Returns
  (missing, out of date) """
  missing = False
  try:
    # Get the render info for the comp
    info = CompSourceInfo(compItem)
    startFrame = info.firstFrame
    endFrame = info.lastFrame

    # If the item is a TrackItem, search for missing files in its source range
    if isinstance(compItem, hiero.core.TrackItem):
      startFrame = int(compItem.sourceIn() + info.firstFrame)
      endFrame = int(compItem.sourceOut() + info.firstFrame)

    # Iterate over the frame range and check if any files are missing. The + 1 is necessary, because range is exclusive at the end of the interval.
    for frame in range(startFrame, endFrame + 1):
      framePath = info.writePath % frame
      try:
        frameModTime = round(filesystem.stat(framePath).st_mtime)
      except OSError as e:
        # Check if file doesn't exist
        if e.errno == errno.ENOENT:
          missing = True
          break
        else:
          raise
  except:
    # Catch all: log, and false will be returned
    hiero.core.log.exception("isCompItemMissingRenders unexpected error")

  return missing


class ProcessorUIBase(IProcessorUI):
  """ProcessorUIBase is the base class from which all Processor UI components must derive.  Defines the UI structure followed
     by the specialised processor UIs. """

  def getTaskItemType(self):
    raise NotImplementedError()

  def __init__(self, preset, itemTypes):
    IProcessorUI.__init__(self)

    self._preset = None
    self._exportTemplate = None
    self._exportStructureViewer = None
    self._contentElement = None
    self._contentScrollArea = None
    self._contentUI = None
    self._editMode = IProcessorUI.ReadOnly
    self._itemTypes = itemTypes
    self._tags = []
    self._project = None
    self._exportItems = []

    self.setPreset(preset)


  def validate ( self, exportItems ):
    """Validate settings in UI. Return False for failure in order to abort export."""
    hiero.core.log.info("ProcessorUIBase validate")
    exportRoot = self._exportTemplate.exportRootPath()
    if exportRoot is None or len(exportRoot)<1:
      msgBox = QtWidgets.QMessageBox()
      msgBox.setText("The export path root is not set, please set a valid path.")
      msgBox.exec_()
      return False
    elif "{projectroot}" in exportRoot:
      project = self.projectFromSelection(exportItems)

      from hiero.ui import getProjectRootInteractive
      projectRoot = getProjectRootInteractive(project)
      if not projectRoot:
        return False

    # Check for offline track items
    if not self.checkOfflineMedia(exportItems):
      return False

    if not self.checkUnrenderedComps(exportItems):
      return False

    return True


  def isTranscodeExport(self):
    """ Check if there are transcode tasks in this export. """

    # To avoid importing the hiero.exporters module here, just check
    # for 'Transcode' in the preset class name.
    for (exportPath, preset) in self._exportTemplate.flatten():
      if "Transcode" in FnExporterBase.classBasename(type(preset)):
        return True
    return False


  def findCompItems(self, items):
    """ Search for comp clips and track items in a list of ItemWrappers. """
    for item in items:
      if item.clip():
        if CompSourceInfo(item.clip()).nkPath:
          yield item.clip()
      else:
        for trackItem in self.toTrackItems([item]):
          try:
            if CompSourceInfo(trackItem).nkPath:
              yield trackItem
          except:
            pass


  def checkUnrenderedComps(self, exportItems):
    """ Check for unrendered comps selected for export and ask the user what to do. """

    hiero.core.log.info("ProcessorUIBase checkUnrenderedComps begin")
    # Only do this check for transcodes
    if not self.isTranscodeExport():
      return True

    hiero.core.log.info("ProcessorUIBase checkUnrenderedComps is transcode export")
    # Scan the items and find comps which haven't been rendered
    unrenderedNkSources = set()
    for compItem in self.findCompItems(exportItems):
      if isinstance(compItem, hiero.core.TrackItem):
        source = compItem.source().mediaSource()
      elif isinstance(compItem, hiero.core.Clip):
        source = compItem.mediaSource()
      hiero.core.log.info("ProcessorUIBase checkUnrenderedComps in loop")
      unrendered = isCompItemMissingRenders(compItem)
      if unrendered:
        unrenderedNkSources.add(source)

    continueExport = True
    renderComps = False

    # Show a message box and give the user the option to either render the comps or skip them
    if unrenderedNkSources:
      messageText = ("Some Comp items have not been rendered or are out of date."
                     " Do you want to render them now, or skip them?")
      messageBox = QtWidgets.QMessageBox( QtWidgets.QMessageBox.Question, "Export", messageText, QtWidgets.QMessageBox.NoButton, hiero.ui.mainWindow() )
      cancelButton = messageBox.addButton( "Cancel export", QtWidgets.QMessageBox.RejectRole )
      messageBox.setDefaultButton( cancelButton )
      renderButton = messageBox.addButton("Render", QtWidgets.QMessageBox.YesRole)
      skipButton = messageBox.addButton("Skip", QtWidgets.QMessageBox.YesRole)
      messageBox.exec_()

      clickedButton = messageBox.clickedButton()
      if clickedButton == cancelButton:
        continueExport = False
      else:
        renderComps = (clickedButton == renderButton)

        # If the user selected 'Render', render all unrendered comps.
        if renderComps:
          compsToRender = unrenderedNkSources
          self._preset.setCompsToRender(compsToRender)
        # If the user selected 'Skip', exclude unrendered comps completely.
        else:
          self._preset.setCompsToSkip(unrenderedNkSources)

    # Otherwise make sure the comps to render list is cleared
    else:
      self._preset.setCompsToRender([])

    return continueExport


  def projectFromSelection(self, items):
    # Return the project of the first item in the selection

    for item in items:
      if item.trackItem():
        return item.trackItem().project()
      elif item.sequence():
        return item.sequence().project()
      elif item.clip():
        return item.clip().project()

    return None


  def toTrackItems(self, items):
    # Filter out tracks which have been excluded in the preset.  This isn't a great solution
    # (we shouldn't really be doing the validation in this class at all), but it works for now.
    excludedTracksGUIDs = []
    if hasattr(self._preset, "_excludedTrackIDs"):
      excludedTracksGUIDs = self._preset._excludedTrackIDs

    for item in items:
      if item.trackItem():
        yield item.trackItem()
      elif item.sequence():
        for track in itertools.chain(item.sequence().videoTracks(), item.sequence().audioTracks()):
          if track.guid() not in excludedTracksGUIDs and track.isEnabled():
            for trackItem in track:
              yield trackItem


  def findOfflineMedia(self, exportItems):
    # Return a tuple containing a list of offline track items, and a list of online ones
    offline = []
    online = []
    for trackItem in self.toTrackItems(exportItems):
      if (not isinstance(trackItem, hiero.core.TrackItem)) or trackItem.source().mediaSource().isMediaPresent():
        online.append(trackItem)
      else:
        offline.append(trackItem)
    return (offline, online)


  def offlineMediaPrompt(self, messageText, messageDetails, hasOnline):
    # Ask the user how they want to proceed when trying to export offline media.
    # They will be given the option to skip or include offline media, or to cancel.
    # Return True if the export should proceed.
    messageBox = QtWidgets.QMessageBox( QtWidgets.QMessageBox.Question, "Export", messageText, QtWidgets.QMessageBox.NoButton, hiero.ui.mainWindow() )
    if messageDetails:
      messageBox.setDetailedText( messageDetails )
    noButton = messageBox.addButton( "Cancel export", QtWidgets.QMessageBox.RejectRole )
    messageBox.setDefaultButton( noButton )
    skipButton = None
    if hasOnline:
      skipButton = messageBox.addButton( "Skip offline", QtWidgets.QMessageBox.YesRole )
    includeButton = messageBox.addButton( "Export offline", QtWidgets.QMessageBox.YesRole )
    messageBox.exec_()
    if messageBox.clickedButton() == skipButton:
      self._preset.setSkipOffline( True )
      return True
    elif messageBox.clickedButton() == includeButton:
      self._preset.setSkipOffline( False )
      return True
    else:
      return False


  def checkOfflineMedia(self, exportItems):
    # Check for track items which has offline media and prompt the user if any are found
    offline, online = self.findOfflineMedia(exportItems)
    if offline:
      messageText = "Some items are offline.  Do you want to continue?"
      messageDetails = "\n".join( [offlineItem.name() + " (MediaOffline)" for offlineItem in offline ] )
      return self.offlineMediaPrompt(messageText, messageDetails, online)
    else:
      return True


  def findTagsForItems(self, exportItems):
    """ Find tags for the export items. """
    return FnExporterBase.tagsFromSelection(exportItems, includeChildren=True)


  def populateUI(self, processorUIWidget, taskUIWidget, exportItems):
    """ Build the processor UI and add it to widget. """
    self._exportItems = exportItems

    self._tags = self.findTagsForItems(exportItems)

    layout = QtWidgets.QVBoxLayout(processorUIWidget)
    layout.setContentsMargins(0, 0, 0, 0)
    splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
    splitter.setChildrenCollapsible(False);
    splitter.setHandleWidth(10);
    layout.addWidget(splitter)
    
    self._editMode = IProcessorUI.ReadOnly if self._preset.readOnly() else IProcessorUI.Full

    # The same enums are declared in 2 classes.  They should have the same values but to be sure, map between them
    editModeMap = { IProcessorUI.ReadOnly : ui.ExportStructureViewer.ReadOnly,
                    IProcessorUI.Limited : ui.ExportStructureViewer.Limited,
                    IProcessorUI.Full : ui.ExportStructureViewer.Full }

    structureViewerMode = editModeMap[self._editMode]
    
    ###EXPORT STRUCTURE
    exportStructureWidget = QtWidgets.QWidget()
    splitter.addWidget(exportStructureWidget)
    exportStructureLayout =  QtWidgets.QVBoxLayout(exportStructureWidget)
    exportStructureLayout.setContentsMargins(0, 0, 0, 9)
    self._exportStructureViewer = ui.ExportStructureViewer(self._exportTemplate, structureViewerMode)
    exportStructureLayout.addWidget(self._exportStructureViewer)
    self._project = self.projectFromSelection(exportItems)
    if self._project:
      self._exportStructureViewer.setProject(self._project)

    self._exportStructureViewer.destroyed.connect(self.onExportStructureViewerDestroyed)

    self._exportStructureViewer.setItemTypes(self._itemTypes)
    self._preset.createResolver().addEntriesToExportStructureViewer(self._exportStructureViewer)
    self._exportStructureViewer.structureModified.connect(self.onExportStructureModified)
    self._exportStructureViewer.selectionChanged.connect(self.onExportStructureSelectionChanged)

    exportStructureLayout.addWidget(self.createVersionWidget())

    exportStructureLayout.addWidget(self.createPathPreviewWidget())

    splitter.addWidget(self.createProcessorSettingsWidget(exportItems))

    taskUILayout = QtWidgets.QVBoxLayout(taskUIWidget)
    taskUILayout.setContentsMargins(10, 0, 0, 0)
    tabWidget = QtWidgets.QTabWidget()
    taskUILayout.addWidget(tabWidget)
    self._contentScrollArea = QtWidgets.QScrollArea()
    tabWidget.addTab(self._contentScrollArea, "Content")
    self._contentScrollArea.setFrameStyle( QtWidgets.QScrollArea.NoFrame )
    self._contentScrollArea.setWidgetResizable(True)


  def setPreset(self, preset):
    """ Set the export preset. """
    self._preset = preset
    oldTemplate = self._exportTemplate

    self._exportTemplate = hiero.core.ExportStructure2()
    self._exportTemplate.restore(self._preset.properties()["exportTemplate"])
    if self._preset.properties()["exportRoot"] != "None":
      self._exportTemplate.setExportRootPath(self._preset.properties()["exportRoot"])

    # Must replace the Export Structure viewer structure object before old template is destroyed
    if self._exportStructureViewer is not None:
      self._exportStructureViewer.setExportStructure(self._exportTemplate)

    # Bug 46032 - Make sure that the task preset shares the same project as its parent.
    # Since the taskUI might require information from the project.
    for (exportPath, taskPreset) in self._exportTemplate.flatten():
      # Preset can be None if the user never set it
      if not taskPreset:
        continue

      taskPreset.setProject(preset.project())

      # Setup callbacks on the task preset.  This is mainly used by the NukeShotPreset,
      # which references other tasks by path and needs to be told when the paths
      # change.
      taskPreset.initialiseCallbacks(self._exportTemplate)


  def preset(self):
    """ Get the export preset. """
    return self._preset


  def setTaskContent(self, preset):
    """ Get the UI for a task preset and add it in the 'Content' tab. """

    # First clear the old task UI.  It's important that this doesn't live longer
    # than the widgets it created, otherwise it can lead to crashes in PySide2.
    self._contentUI = None

    taskUIWidget = None

    # if selection is valid, grab preset
    if preset is not None:
      # Get a new TaskUI object from the registry
      taskUI = hiero.ui.taskUIRegistry.getNewTaskUIForPreset(preset)
      # if UI is valid, set preset and add to 'contentlayout'
      if taskUI:
        # Set the project on the task UI.  It may need it to show project-specific
        # information, e.g. colorspace configs.
        taskUI.setProject(self._project)
        taskUI.setTags(self._tags)

        taskUIWidget = QtWidgets.QWidget()

        taskUI.setTaskItemType(self.getTaskItemType())
        # Initialize and Populate UI
        taskUI.initializeAndPopulateUI(taskUIWidget, self._exportTemplate)
        self._contentUI = taskUI

        if self._editMode == IProcessorUI.ReadOnly:
          taskUIWidget.setEnabled(False)

        try:
          taskUI.propertiesChanged.connect(self.onExportStructureModified,
                                           type=QtCore.Qt.UniqueConnection)
        except:
          # Signal already connected.
          pass

    # If there's no task UI, create an empty widget.
    if not taskUIWidget:
      taskUIWidget = QtWidgets.QWidget()

    # Add the task UI widget to the scroll area
    self._contentScrollArea.setWidget( taskUIWidget )


  def onExportStructureModified(self):
    """ Callback when the export structure is modified by the user. """

    self._preset.properties()["exportTemplate"] = self._exportTemplate.flatten()
    self._preset.properties()["exportRoot"] = self._exportTemplate.exportRootPath()
    if self._exportStructureViewer and self._contentElement is not None:
      self._exportStructureViewer.refreshContentField(self._contentElement)
    self.updatePathPreview()


  def onExportStructureSelectionChanged(self):
    """ Callback when the selection in the export structure viewer changes. """
    # Grab current selection
    element = self._exportStructureViewer.selection()
    if element is not None:
      self._contentElement = element
      self.setTaskContent(element.preset())
    self.updatePathPreview()


  def onExportStructureViewerDestroyed(self):
    """ Callback when the export structure viewer is destroyed.  Qt will delete it while we still
        have a reference, so reset to None when the destroyed() signal is emitted. """
    self._exportStructureViewer = None


  def createProcessorSettingsWidget(self, exportItems):
    """ Create the UI for processor-specific settings.  To be reimplemented by subclasses. """
    raise NotImplementedError()


  def processorSettingsLabel(self):
    """ Get the label which is put on the tab for processor-specific settings.  To be reimplemented by subclasses. """
    raise NotImplementedError()


  def savePreset( self ):
    """ Save the export template to the preset. """
    self._preset.properties()["exportTemplate"] = self._exportTemplate.flatten()
    self._preset.properties()["exportRoot"] = self._exportTemplate.exportRootPath()


  def createVersionWidget(self):
    """ Create a widget for selecting the version number for export. """
    widget = QtWidgets.QWidget()
    layout = QtWidgets.QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    widget.setLayout(layout)

    # Version custom versionSpinBox widget - allows user to specify padding
    versionToolTip = "Set the version number for files/scripts which include the {version} token in the path.\nThis box sets the version number string (#) in the form: v#, e.g. 01 > v01.\nUse the +/- to control padding e.g. v01 / v0001."

    versionLayout = QtWidgets.QHBoxLayout()

    versionLabel = QtWidgets.QLabel("Version token number:")
    layout.addWidget(versionLabel)

    versionSpinBox = hiero.ui.VersionWidget()
    versionSpinBox.setToolTip(versionToolTip)
    versionSpinBox.setValue(self._preset.properties()["versionIndex"])
    versionSpinBox.setPadding(self._preset.properties()["versionPadding"])
    versionSpinBox.valueChanged.connect(self.onVersionIndexChanged)
    versionSpinBox.paddingChanged.connect(self.onVersionPaddingChanged)
    layout.addWidget(versionSpinBox)
    layout.addStretch()

    return widget


  def onVersionIndexChanged(self, value):
    """ Callback when the version index changes. """
    self._preset.properties()["versionIndex"] = int(value)
    self.updatePathPreview()


  def onVersionPaddingChanged(self, padding):
    """ Callback when the version padding changes. """
    self._preset.properties()["versionPadding"] = int(padding)
    self.updatePathPreview()


  def createPathPreviewWidget(self):
    """ Create a widget for showing a preview of the expanded export path. """
    self._pathPreviewWidget = ElidedLabel()
    return self._pathPreviewWidget


  def updatePathPreview(self):
    """ Update the path preview widget for the currently selected item in the
    tree view.
    """
    text = ""
    try:
      selectedElement = self._exportStructureViewer.selection()
      if selectedElement:
        # Find the first leaf element, which should have a preset associated
        # with it that can be used to resolve the path. If a directory element
        # has been selected, that will still have a TaskPresetBase associated with
        # it for some reason, but that can't be used to create tasks.
        def findLeafElementRecursive(element):
          children = element.children()
          if not children:
            return element
          else:
            return findLeafElementRecursive(children[0])
        taskElement = findLeafElementRecursive(selectedElement)
        taskPreset = taskElement.preset()
        # Create a processor and generate tasks for the current export
        processor = hiero.core.taskRegistry.createProcessor(self._preset)
        tasks = processor.startProcessing(self._exportItems, preview=True)
        # Find the first task which matches the selected preset. If there are
        # multiple items being selected, the first in the list is displayed,
        # which is enough to give the user an idea of how their path template
        # will be expanded
        for task in tasks:
          if task._preset is taskPreset:
            exportRoot = self._exportTemplate.exportRootPath()
            path = os.path.join(exportRoot, selectedElement.path())
            text = "Preview: %s" % task.resolvePath(path)
            break
    except:
      hiero.core.log.exception("Error generating path preview")
    self._pathPreviewWidget.setText(text)


  def skipOffline(self):
    return self._preset.skipOffline()


  def refreshContent(self):
    """ Refresh the content area of this ProcessorUI """
    element = self._exportStructureViewer.selection() if self._exportStructureViewer else None
    if element is not None:
      currentVerticalScrollPosition = self._contentScrollArea.verticalScrollBar().value()
      self._contentElement = element
      self.setTaskContent(element.preset())
      self._contentScrollArea.verticalScrollBar().setValue(currentVerticalScrollPosition)
