
import hiero.ui
import hiero.core
import os.path
import itertools
import sys
import traceback
import threading
from hiero.ui.BuildExternalMediaTrack import BuildTrack, BuildTrackFromExportTagAction, TrackFinderByTag
from PySide2 import(QtCore, QtGui, QtWidgets)

from hiero.core import nuke
from hiero.core import log
from hiero.ui.FnPathQueryDialog import *
from hiero.ui import InvalidOutputResolutionMessage
from hiero.core.VersionScanner import VersionScanner
from . send_to_nuke import TrackItemCollisionDialog, getProjectShotPreset
from _fnpython import showCreateCompSpecialDialog, viewIconForTrack
from foundry.ui import showDismissibleWarning
from nuke import executeInMainThread

from hiero.ui.nuke_bridge import FnNsFrameServer as postProcessor


def getRenderOutputType(preset):
  """ Get the file type from the preset's Write node. """

  kNukeShotTaskName = 'hiero.exporters.FnNukeShotExporter.NukeShotExporter'
  kWriteNodeTaskName = 'hiero.exporters.FnExternalRender.NukeRenderTask'

  # First find the Nuke Shot Exporter and get the Write node path from it.
  # It will be either the one specified in the preset using key "timelineWriteNode"
  # or the first one in the list if none is specified. If we fail to find any
  # write node, throw an exception
  writeNodePath = None
  for itemPath, itemPreset in preset.properties()["exportTemplate"]:
    if itemPreset and itemPreset.ident() == kNukeShotTaskName:
      writeNodePath = itemPreset.properties()["timelineWriteNode"]
      if not writeNodePath:
        if itemPreset.properties()["writePaths"]:
          writeNodePath = itemPreset.properties()["writePaths"][0]
      break

  if not writeNodePath:
    raise RuntimeError("Your Export Structure has no Write Nodes defined.")

  # Next find the Write node preset corresponding to the path, and return its file_type property.
  for itemPath, itemPreset in preset.properties()["exportTemplate"]:
    if itemPreset and itemPreset.ident() == kWriteNodeTaskName and itemPath == writeNodePath:
      return itemPreset.properties()["file_type"]

  # The preset should already have been validated to the extent that we can find the Write node.  If not, raise an error
  raise RuntimeError("Failed to get render output type")


def checkPresetRenderOutput(preset):
  """ Check if the render output of the export preset is supported by create comp.  Only rendering to image sequences is allowed at the moment. """

  kMovieFileTypes = ("mov", "mov64", "ffmpeg", "mxf")

  renderOutputType = getRenderOutputType(preset)
  if renderOutputType in kMovieFileTypes:
    QtWidgets.QMessageBox.warning(hiero.ui.mainWindow(), "Create Comp",  "Cannot create a comp with Write node file type set to '%s'.  Only rendering to image sequences is currently supported." % renderOutputType)
    return False

  return True


class CreateCompShotTableDelegate(QtWidgets.QStyledItemDelegate):
  """ Delegate for the table view in the create comp dialog. Allows for customising
  the icon size, and adding a left margin.
  """
  def __init__(self, iconSize, leftMargin, parent=None):
    QtWidgets.QStyledItemDelegate.__init__(self, parent)
    self.iconSize = iconSize
    self.leftMargin = leftMargin

  def paint(self, painter, option, index):
    # Set the icon size
    option.decorationSize = self.iconSize
    # Account for left margin
    option.rect.setLeft(option.rect.left() + self.leftMargin)
    QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)

  def sizeHint(self, option, index):
    # Set the icon size
    option.decorationSize = self.iconSize
    # Account for left margin
    size = QtWidgets.QStyledItemDelegate.sizeHint(self, option, index)
    size.setWidth(size.width() + self.leftMargin)
    return size

# Role for storing the track index, used in sorting
kModelTrackIndexRole = QtCore.Qt.UserRole + 1

# Model columns
kModelTrackNameColumn = 0
kModelShotNameColumn = 1
kModelTimesColumn = 2

class CreateCompShotTableSortModel(QtCore.QSortFilterProxyModel):
  """ Proxy model for sorting shots. Overrides the defaults so
  a) times are sorted numerically
  b) for items which compare equal, breaks the tie by comparing track indexes
  """
  def __init__(self):
    QtCore.QSortFilterProxyModel.__init__(self)

  def _lessThanHelper(self, source_left, source_right):
    # For the times column, compare the values, first on the start time then on the end time
    if source_left.column() == kModelTimesColumn and source_right.column() == kModelTimesColumn:
      leftTimes = [ int(s) for s in source_left.data().split('-') ]
      rightTimes = [ int(s) for s in source_right.data().split('-') ]
      return leftTimes[0] < rightTimes[0] or (leftTimes[0] == rightTimes[0] and leftTimes[1] < rightTimes[1])
    else:
      return QtCore.QSortFilterProxyModel.lessThan(self, source_left, source_right)

  def lessThan(self, source_left, source_right):
    # First compare the data in the indexes, if they're equal, compare the track indexes
    isLessThan = self._lessThanHelper(source_left, source_right)
    isEqual = not isLessThan and not self._lessThanHelper(source_right, source_left)
    if isEqual:
      isLessThan = source_left.data(kModelTrackIndexRole) < source_right.data(kModelTrackIndexRole)
    return isLessThan


class CreateCompForTrackItemsDialog(QtWidgets.QDialog):
  kWindowTitle = "Create Comp"
  kCompTypeLabel = "How do you want to create the comp:"
  kSingleNukeText = "Single comp for all selected shots"
  kMultiNukeText = "Separate comp for each selected shot"
  kMasterTableLabel = "Select a master shot for your comp:"
  kMasterShotTooltip = ("When applying a single effect across all shots you will need "
                        "to select a shot to use as the 'master' shot for this effect.\n"
                        "The master shot defines the start frame range from which other "
                        "shots are offset when merged down into a single effect shot")
  kSelectPresetButtonTooltip = ("Select or configure the preset to use for creating comps.")

  def __init__(self, trackItems, preset, parent=None):
    QtWidgets.QDialog.__init__(self, parent)
    self._trackItems = trackItems
    self._preset = preset
    self._multiComp = False

    self.setWindowTitle(CreateCompForTrackItemsDialog.kWindowTitle)

    # Main layout arranged vertically
    mainLayout = QtWidgets.QVBoxLayout(self)
    marginL, marginT, marginR, marginB = mainLayout.getContentsMargins()
    marginT = 5
    mainLayout.setContentsMargins(marginL, marginT, marginR, marginB)

    # Horizontal layout for top half of dialog, with comp type radio buttons on
    # left and button for showing export dialog on the right
    topLayout = QtWidgets.QHBoxLayout()
    mainLayout.addLayout(topLayout)

    # Comp type buttons
    buttonLayout = QtWidgets.QVBoxLayout()
    topLayout.addLayout(buttonLayout)
    buttonLayout.addSpacing(6)
    buttonLayout.addWidget( self.createLabel(CreateCompForTrackItemsDialog.kCompTypeLabel) )
    buttonLayout.addSpacing(5)
    singleCompButton, multiCompButton = self.createCompTypeButtons()
    buttonLayout.addWidget( singleCompButton )
    buttonLayout.addWidget( multiCompButton )

    # Preset button
    selectPresetButton = self.createSelectPresetButton()
    topLayout.addWidget(selectPresetButton, 0, QtCore.Qt.AlignRight|QtCore.Qt.AlignTop)

    # Table widget
    self._tableWidget = QtWidgets.QWidget()
    tableLayout = QtWidgets.QVBoxLayout(self._tableWidget)
    tableLayout.setContentsMargins(0, 0, 0, 0)
    tableLayout.addSpacing(15)
    tableLayout.addWidget( self.createLabel(CreateCompForTrackItemsDialog.kMasterTableLabel) )
    tableLayout.addSpacing(5)
    self._trackItemTable = self.createShotsTableWidget()
    tableLayout.addWidget( self._trackItemTable )
    mainLayout.addWidget(self._tableWidget)

    # Ok/Cancel buttons
    buttonBox = QtWidgets.QDialogButtonBox( QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel )
    buttonBox.accepted.connect( self.accept )
    buttonBox.rejected.connect( self.reject )
    mainLayout.addWidget( buttonBox )


  def createLabel(self, text):
    """ Create a label with the font set to bold """
    label = QtWidgets.QLabel(text)
    font = label.font()
    font.setBold(True)
    label.setFont(font)
    return label

  def createCompTypeButtons(self):
    """ Create radio buttons for selecting between single/multi comp """
    buttonGroup = QtWidgets.QButtonGroup(self)
    singleCompButton = QtWidgets.QRadioButton(CreateCompForTrackItemsDialog.kSingleNukeText)
    singleCompButton.setChecked( True )
    singleCompButton.clicked.connect( self._onsingleCompButtonClicked )
    multiCompButton = QtWidgets.QRadioButton(CreateCompForTrackItemsDialog.kMultiNukeText)
    multiCompButton.clicked.connect( self._onmultiCompButtonClicked )
    buttonGroup.addButton( singleCompButton, 0 )
    buttonGroup.addButton( multiCompButton, 1 )

    return singleCompButton, multiCompButton

  def createSelectPresetButton(self):
    """ Create the button for showing the Create Comp Special dialog """
    selectPresetButton = QtWidgets.QPushButton()
    selectPresetButton.setFlat(True)
    selectPresetButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    selectPresetButton.setToolTip(CreateCompForTrackItemsDialog.kSelectPresetButtonTooltip)
    selectPresetButton.setIcon(QtGui.QIcon("icons:SettingsButton.png"))
    selectPresetButton.clicked.connect(self._openCreateCompSpecialDialog)
    return selectPresetButton

  def createShotsTableWidget(self):
    """ Create the table for selecting the master track item """
    # Build the model
    model = QtGui.QStandardItemModel(len(self._trackItems), 3)
    model.setHorizontalHeaderLabels(("Track Name", "Shot Name", "Timeline Range"))
    for index, item in enumerate(self._trackItems):
      track = item.parent()
      trackModelItem = QtGui.QStandardItem(track.name())
      trackViewIcon = viewIconForTrack(item.parent())
      trackModelItem.setData(track.trackIndex(), kModelTrackIndexRole)
      if trackViewIcon:
        trackModelItem.setIcon(trackViewIcon)
      model.setItem(index, kModelTrackNameColumn, trackModelItem)
      shotModelItem = QtGui.QStandardItem(item.name())
      shotModelItem.setIcon(QtGui.QIcon(QtGui.QPixmap.fromImage(item.thumbnail())))
      shotModelItem.setData(track.trackIndex(), kModelTrackIndexRole)
      model.setItem(index, kModelShotNameColumn, shotModelItem)
      timelineTimeItem = QtGui.QStandardItem(str(item.timelineIn()) + '-' + str(item.timelineOut()))
      timelineTimeItem.setTextAlignment(QtCore.Qt.AlignCenter)
      timelineTimeItem.setData(track.trackIndex(), kModelTrackIndexRole)
      model.setItem(index, kModelTimesColumn, timelineTimeItem)

    # Create a proxy model to allow sorting
    sortModel = CreateCompShotTableSortModel()
    sortModel.setSourceModel(model)

    # Create the table view
    table = QtWidgets.QTableView()
    table.setAlternatingRowColors(True)
    table.setShowGrid(False)
    table.setWordWrap(True)
    table.setToolTip(CreateCompForTrackItemsDialog.kMasterShotTooltip)
    table.setEditTriggers( QtWidgets.QAbstractItemView.NoEditTriggers )
    table.verticalHeader().setVisible(False)
    header = table.horizontalHeader()
    header.setStretchLastSection( True )
    table.setMinimumWidth(380)
    table.setModel(sortModel)
    table.setSortingEnabled(True)
    table.sortByColumn(2, QtCore.Qt.AscendingOrder)
    table.setItemDelegateForColumn(0, CreateCompShotTableDelegate(QtCore.QSize(16, 16), 10, table))
    table.setItemDelegateForColumn(1, CreateCompShotTableDelegate(QtCore.QSize(70, 40), 10, table))
    table.setItemDelegateForColumn(2, CreateCompShotTableDelegate(QtCore.QSize(70, 40), 10, table))

    # Set the selection mode and select the first row
    table.setSelectionBehavior( QtWidgets.QAbstractItemView.SelectRows )
    table.setSelectionMode( QtWidgets.QAbstractItemView.SingleSelection )
    table.selectionModel().select(sortModel.index(0, 0), QtCore.QItemSelectionModel.SelectCurrent| QtCore.QItemSelectionModel.Rows)

    header.resizeSection(0, 118)
    header.resizeSection(1, 240)
    return table

  def _onsingleCompButtonClicked(self):
    self._multiComp = False
    self._setTableVisibility(True)

  def _onmultiCompButtonClicked(self):
    self._multiComp = True
    self._setTableVisibility(False)

  def _setTableVisibility(self, visible):
    """ Set the visibility of the table, adjusting the dialog size accordingly. """
    if visible == self._tableWidget.isVisible():
      return

    oldHeight = self.height()
    if visible:
      newHeight = oldHeight + self._tableHeight
    else:
      self._tableHeight = self._tableWidget.height()
      newHeight = self.height() - self._tableHeight
    self._tableWidget.setVisible(visible)
    QtCore.QCoreApplication.processEvents()
    self.resize(self.width(), newHeight)

  def _openCreateCompSpecialDialog(self):
    """ Open the Create Comp Special dialog allowing the user to configure the preset from here """
    newPreset = showCreateCompSpecialDialog(self._trackItems)
    if newPreset:
      self._preset = newPreset

  def multipleComps(self):
    """ Get if creating a comp for each track item was selected """
    return self._multiComp
    
  def masterTrackItem(self):
    """ For a single comp, get the selected master track item """
    proxyIndex = self._trackItemTable.selectedIndexes()[0]
    index = self._trackItemTable.model().mapToSource(proxyIndex)
    return self._trackItems[ index.row() ]

  def preset(self):
    """ Get the export preset to use for the comp """
    return self._preset

  def sizeHint(self):
    return QtCore.QSize(520, 400)


class CreateCompMessageBoxErrorHandler(object):
  """ Class which handles error messages in Create Comp by showing a message box. """

  kDefaultBriefMessage = "An error occurred during script export."

  def error(self, message):
    """ Handle an error message.  Currently shows a message box with the error text. """
    detail = message
    brief = self.getBriefTextFromMessage(message) or CreateCompMessageBoxErrorHandler.kDefaultBriefMessage
    self.showErrorDialog(brief, detail)


  def getBriefTextFromMessage(self, message):
    """ Extract the error message from the text.  Due to the way the export system handles errors, the
        message that Create Comp gets is usually in the form of a full stack trace from the original exception.
        Try to find the exception message in that. """
    for line in reversed(message.splitlines()):
       if line.startswith("Exception:"):
         return line[11:]


  def showErrorDialog(self, brief, detail):
    """ Show an error message box with the brief and detailed text. """
    msgBox = QtWidgets.QMessageBox(hiero.ui.mainWindow())
    msgBox.setText("Create Comp Error")
    msgBox.setInformativeText(brief)
    msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
    msgBox.setDetailedText(detail)
    msgBox.exec_()



class CreateCompActionBase(BuildTrackFromExportTagAction):
  def __init__(self, trackItems, effectItems, annotations, title):
    BuildTrackFromExportTagAction.__init__(self)

    self.trackFinder = TrackFinderByTag(self)

    self.setText(title)

    # store the track name, currently hardcoded, for later
    self._trackName = BuildTrack.ProjectTrackNameDefault(trackItems)
    self._trackItems = trackItems
    self._effectItems = effectItems
    self._annotations = annotations

    # List of track items showing the comps.  This should include already existing items and
    # ones we're going to create
    self._compTrackItems = []

    # If taskRegistry is available, always enable because an export can be invoked to create the script
    self.setEnabled((hasattr(hiero.core, "taskRegistry") and (len(self._trackItems) > 0)))

    self._progressTask = None
    self._success = False
    self._cancelled = False

    self._errorHandler = CreateCompMessageBoxErrorHandler()


  def findTag(self, trackItem):
    """ Override from base class.  Find the Nuke Shot Exporter tag. """
    return self.findShotExporterTag(trackItem)


  def findExistingCreateCompTag(self, trackItem):
    """ Try to find a tag from a previous 'Create Comp' by checking that it has the expected metadata keys.
        Crucially, it should have the 'tag.trackItem' key indicating the tag had a comp track item created from it. """
    return self._findTagWithMetadataKeys(trackItem, ("tag.presetid", "tag.path", "tag.script", "tag.trackItem"))


  def _nukeExportInfo(self, tag):
    metadata = tag.metadata()
    assert metadata.hasKey("tag.path")
    assert metadata.hasKey("tag.script")
    return (metadata["tag.script"], metadata["tag.script"])


  def trackItemAdded(self, newTrackItem, track, originalTrackItem):
    # this is called when the new VFX track is created; keep track of the items
    self._compTrackItems.append(newTrackItem)

    BuildTrackFromExportTagAction.trackItemAdded(self, newTrackItem, track, originalTrackItem)
    

  def _buildTrackItem(self, name, clip, originalTrackItem, expectedStartTime, expectedDuration, expectedStartHandle, expectedEndHandle, expectedOffset):

    # When writing a single Nuke script calculate the timeline extent of all the selected items to build the new track item
    if self._singleNukeScript:
      timelineIn, timelineOut = sys.maxsize, 0
      #  Timeline range is the min/max of all trackitems
      for trackItem in self._trackItems:
        timelineIn = min(trackItem.timelineIn(), timelineIn)
        timelineOut = max(trackItem.timelineOut(), timelineOut)

      sourceIn = expectedStartHandle
      sourceOut = (expectedDuration - 1) - expectedEndHandle

      trackItem = hiero.core.TrackItem(name, hiero.core.TrackItem.kVideo)

      # Assign new clip
      trackItem.setSource(clip)
      trackItem.setTimes(timelineIn, timelineOut, sourceIn, sourceOut)

      return trackItem

    # Otherwise use the base class implementation
    else:
      return super(CreateCompActionBase, self)._buildTrackItem(name, clip, originalTrackItem, expectedStartTime, expectedDuration, expectedStartHandle, expectedEndHandle, expectedOffset)


  def getExternalFilePaths(self, trackItem):
    # For 'Create Comp' the external path we're interested in is the Nuke script itself,
    # not the output.
    tag = self.findShotExporterTag(trackItem)
    if tag and tag.metadata().hasKey("script"):
      return tag.metadata().value("script").split(';')
    else:
      return None


  def _setPresetTaskProperties(self, preset, **properties):
    for path, taskPreset in preset.properties()["exportTemplate"]:
      if taskPreset:
        taskProperties = taskPreset.properties()
        for key, value in properties.items():
          if key in taskProperties:
            taskProperties[key] = value


  def _preProcessTrackItems(self, trackItems):
    """ Check tags and versions on the given track items prior to exporting them.  This will return a list of tuples,
        containing (trackItem, tag, version).   If there was no tag already on the item, it will be None. """
        
    foundTag = False
    trackItemData = []
    for trackItem in trackItems:
      version = 1
      tag = self.findExistingCreateCompTag(trackItem)
      # If there's an existing tag on this track item, figure out what the new version is.
      if tag:
        foundTag = True

        path = tag.metadata().value("tag.script")
        if hiero.core.util.filesystem.exists(path):
          try:
            # Determine the new version
            versionScanner = VersionScanner()
            version = versionScanner.getNewVersionIndexForPath(path)
          except:
            response = QtWidgets.QMessageBox.warning(
                hiero.ui.mainWindow(),
                "Create Comp", "No versions found in export path.  Do you want to overwrite?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if response == QtWidgets.QMessageBox.No:
              continue
        else:
          # If the script named in the tag didn't exist, just remove it and continue the export.
          trackItem.removeTag(tag)
          tag = None

      trackItemData.append( (trackItem, tag, version) )

    if foundTag:
      # Warn the user they might be overwriting a file and give them the option to cancel
      ok = self._warnExistingExport()
      if not ok:
        return []
      
    return trackItemData


  def _layoutScripts(self, trackItemData):
    """ Layout all the scripts we've created from the items in trackItemData.  This will be run on 
        a background thread to keep the UI responsive, since this can be slow, especially on Windows. """
        
    counter = 0.0
    total = len(trackItemData) + 1.0 # Add 1 to the total so the progress doesn't go to 100% in this phase

    for trackItem, tag, version in trackItemData:
      if not tag:
        tag = self.findShotExporterTag(trackItem)

      if tag:
        scriptPath = tag.metadata()["tag.script"]
        error = postProcessor.postProcessScript(scriptPath)
        if error:
          executeInMainThread(QtWidgets.QMessageBox.warning, args=(
            hiero.ui.mainWindow(),
            "Script Post Processor",
            "An error has occurred while preparing script:\n%s" % error,
          ))
          self._cancelled = True
        
      if self._isCancelled():
        return

      # Set the progress.  Execute in the main thread since it will be calling through to the UI
      hiero.core.executeInMainThread( self._setProgress, counter / total * 100 )
      counter = counter + 1
    

  def _setProgress(self, progress):
    """ Set the progress in the UI. """
    if self._progressTask:
      self._progressTask.setProgress( int(progress) )
      
      
  def _isCancelled(self):
    """ Check if the user has cancelled the operation. """
    return self._cancelled or self._progressTask and self._progressTask.isCancelled()
    
    
  def _showProgress(self):
    """ Show the progress window if it's not already visible. """
    if not self._progressTask:
      self._progressTask = foundry.ui.ProgressTask("Creating Comp...")

      
  def _processExportedTrackItems(self, trackItemData, sequence, project):
    """ After writing out the nk scripts, finish processing and build the 
        track with the comp clips on. """

    hiero.core.log.info( "  laying out scripts" )
    layoutNodesThread = threading.Thread(target=self._layoutScripts, args=(trackItemData,))
    layoutNodesThread.start()

    while layoutNodesThread.isAlive():
      QtCore.QCoreApplication.processEvents()

    # Check if the user has cancelled
    if self._isCancelled():
      return

    # Determine which track items we need to create a new clip for.  If there was a comp tag already on the item
    # we can just update the existing comp track item to the new version.
    trackItemsToBuildFrom = []
    for trackItem, tag, version in trackItemData:
      if tag:
        compTrackItem = self._findTrackItemByUID( trackItem.sequence(), tag.metadata().value("tag.trackItem") )
        if compTrackItem:
          CreateCompAction.updateVersions(compTrackItem)
          self._compTrackItems.append(compTrackItem)
        else:
          trackItemsToBuildFrom.append(trackItem)
      else:
        trackItemsToBuildFrom.append(trackItem)

    if trackItemsToBuildFrom:
      if not self._handleMismatchedTracks(trackItemsToBuildFrom, sequence, project):
        return

      # default the track name that we might create with the name of the first track item with a useful tag on it
      foundTrackName = self._findTrackName(sequence)

      if not self._singleNukeScript:
        transitions = self.findTransitionsToCopy(trackItemsToBuildFrom)
      else:
        transitions = []

      # try to build the new track now, from the selected track items that didn't already have tags mapping to a track
      self._buildTrack(trackItemsToBuildFrom + transitions, sequence, project)

    if self._compTrackItems:
      self._success = True


  def findTransitionsToCopy(self, trackItems):
    """ Find transitions which should be copied to the VFX track. """
    transitions = []

    # Helper function for checking if dissolves should be copied.  This is done if either a comp is being created for the other
    # side of the dissolve, or a comp has already been created for it.  The latter is done be checking if it has a tag with the 'trackItem'
    # metadata key.
    def isOtherDissolveItemValid(item):
      if item:
        tag = self.findTag(item)
        if item in trackItems or (tag and tag.metadata().hasKey("tag.trackItem")):
          return True
      return False

    for item in trackItems:
      inTransition = item.inTransition()
      if inTransition and inTransition not in transitions:
        if inTransition.alignment() != hiero.core.Transition.kDissolve or isOtherDissolveItemValid(inTransition.inTrackItem()):
          transitions.append(inTransition)

      outTransition = item.outTransition()
      if outTransition and outTransition not in transitions:
        if outTransition.alignment() != hiero.core.Transition.kDissolve or isOtherDissolveItemValid(outTransition.outTrackItem()):
          transitions.append(outTransition)

    return transitions


  def _exportSequence( self, trackItems, masterTrackItem, version,
                       effectItems, annotations, project):
    """ Export a sequence. """

    preset = hiero.core.taskRegistry.copyPreset(self.shotPreset) # Copy the preset so we can modify its properties
    preset.properties()["versionIndex"] = version

    # If the preset start frame is set to Custom, leave it at that. Otherwise
    # force it to use the track item timeline times.
    startFrameSource = preset.properties()["startFrameSource"]
    if startFrameSource != "Custom":
      preset.properties()["startFrameIndex"] = masterTrackItem.timelineIn()
      preset.properties()["startFrameSource"] = "Custom"

    # With Create Comp, the user has explicitly selected the shots to be exported.
    # Make sure offline ones are included.
    preset.setSkipOffline(False)

    # Override parameters on Project Shot Preset
    # Collate sequence flag is only used here, its purpose is to indicate
    # all other trackitems in sequence should be included in generated nuke script

    #set the postProcessScript to False it will be done on a background
    #thread by create comp

    self._setPresetTaskProperties(preset,
                                  collateSequence=True,
                                  postProcessScript=False)

    # Create export items for the included track items. This uses an odd mechanism
    # where all the track items apart from the master have an 'ignore' flag set.
    # This is used by the ShotProcessor class which includes them on the sequence
    # it builds but doesn't generate tasks for them.
    # For multi-view projects need to find any items for other views and include
    # those. For the master, these will also be added to the export item with
    # setTrackItemsForViews(), so the export code knows to treat these as
    # extra 'master' items
    exportItems = []
    for trackItem in trackItems:
      isMaster = (trackItem == masterTrackItem)
      ignore = not isMaster
      trackItemWrapper = hiero.core.ItemWrapper(trackItem, ignore)
      exportItems.append(trackItemWrapper)
      multiViewTrackItems = self._findMultiViewTrackItems(trackItem)
      if multiViewTrackItems:
        if isMaster:
          trackItemWrapper.setTrackItemsForViews(multiViewTrackItems)

        # Add entry for the track items for other views if not already in the list
        for viewItem in multiViewTrackItems:
          if viewItem not in trackItems:
            exportItems.append(hiero.core.ItemWrapper(viewItem, True))

    # Add in any effects selected effects to the exporter
    exportItems.extend( [hiero.core.ItemWrapper(effect) for effect in effectItems] )
    exportItems.extend( [hiero.core.ItemWrapper(annotation) for annotation in annotations] )

    self._runExport(preset, exportItems)


  def _warnExistingExport(self):
    """ If a comp has already been created for a track item, we will create a new version.  Pop up
        a message box in this case so the user can cancel if they want to. """
    title = "Create Comp"
    text = "Previous export(s) found, continuing will result in a new version of the existing exported script being written."
    infoText = "Do you want to continue?"
    msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, title, text)
    msgBox.setInformativeText(infoText)
    continueButton = msgBox.addButton("Continue", QtWidgets.QMessageBox.AcceptRole)
    msgBox.setDefaultButton(continueButton)
    msgBox.addButton(QtWidgets.QMessageBox.Cancel)
    msgBox.exec_()
    return (msgBox.clickedButton() == continueButton)


  def _exportShots(self, trackItemData, effectItems, annotations, project):
    """ Export track items as separate clips. """
    
    exportEffectList = [hiero.core.ItemWrapper(effect) for effect in effectItems]
    exportAnnotationList = [hiero.core.ItemWrapper(annotation) for annotation in annotations]

    for trackItem, tag, version in trackItemData:
      QtCore.QCoreApplication.processEvents()
      if self._isCancelled():
        return
      
      preset = hiero.core.taskRegistry.copyPreset(self.shotPreset) # Copy the preset so we can modify its properties
      preset.properties()["versionIndex"] = version # Set the version on the preset

      # With Create Comp, the user has explicitly selected the shots to be exported.
      # Make sure offline ones are included.
      preset.setSkipOffline(False)

      #set the postProcessScript to False it will be done on a background
      #thread by create comp
      self._setPresetTaskProperties(preset,
                                    postProcessScript=False)

      trackItemWrapper = hiero.core.ItemWrapper(trackItem)

      # Find track items for other views and include them in the export
      multiViewTrackItems = self._findMultiViewTrackItems(trackItem)
      if multiViewTrackItems:
        trackItemWrapper.setTrackItemsForViews(multiViewTrackItems)

      exportItems = [trackItemWrapper] + exportEffectList + exportAnnotationList
      self._runExport(preset, exportItems)

  def _runExport(self, preset, exportItems):
    """ Run the export from a configured preset and list of items """
    # First run the pre-export validation step and throw if it fails
    errorString = hiero.core.taskRegistry.validateExport(preset, exportItems)
    if errorString:
      raise RuntimeError(errorString)

    # Perform the export
    hiero.core.taskRegistry.createAndExecuteProcessor(preset, exportItems, synchronous=True)

  def _findMultiViewTrackItems(self, mainTrackItem):
    """ For multi-view projects, if the given track item is on a track which
    outputs to a single view, try to find the corresponding items on other tracks
    so they can be included in the exported script. If this is not the case,
    returns None. If the items couldn't be found, throws
    """
    mainTrack = mainTrackItem.parent()
    if not mainTrack.view():
      return None
    foundItems = []
    project = mainTrackItem.project()
    views = set(project.views())
    views.remove(mainTrack.view())
    sequence = mainTrack.parent()
    for track in sequence.videoTracks():
      trackView = track.view()
      if trackView and trackView in views:
        for trackItem in track:
          # For the moment, match only if using the same clip and the timing is
          # the same. This may become more sophisticated and/or allow the user to select
          matches = (trackItem.timelineIn() == mainTrackItem.timelineIn()
                      and trackItem.source() == mainTrackItem.source())
          if matches:
            foundItems.append(trackItem)
            views.remove(trackView)
            break

    return foundItems

  def _findTrackByUID(self, sequence, uid):
    for track in sequence:
      if track.guid() == uid:
        return track
    return None

  def _findTrackItemByUID(self, sequence, uid):
    for track in sequence.videoTracks():
      for item in track:
        if item.guid() == uid:
          return item
    return None

  def _selectTrackName(self, trackNamePossibilities):
    # allow the user to select which track to build to
    dialog = QtWidgets.QDialog(hiero.ui.mainWindow())
    dialog.setWindowTitle("NukeStudio")
    dialog.setSizeGripEnabled(True)

    layout = QtWidgets.QVBoxLayout()

    label = QtWidgets.QLabel("The selected track items have tags that apply to different target tracks. Please select the target track you'd like the external media track items to be placed onto:")
    label.setMinimumWidth(200)
    label.setWordWrap(True)
    layout.addWidget(label)

    trackCombo = QtWidgets.QComboBox()
    for name in trackNamePossibilities:
      trackCombo.addItem(name)
    trackCombo.setCurrentIndex(0)
    layout.addWidget(trackCombo)

    buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
    buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setDefault(True)
    buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setToolTip("Causes the new external media track items to be created on the selected target track.")
    buttonbox.accepted.connect(dialog.accept)
    buttonbox.rejected.connect(dialog.reject)
    layout.addWidget(buttonbox)

    dialog.setLayout(layout)

    if (dialog.exec_() != QtWidgets.QDialog.DialogCode.Accepted):
      return None

    return trackCombo.currentText()

  def _findTrackName(self, sequence):
    # find the first track item that has a tag
    foundTrackName = False
    for trackItem in self._trackItems:
      tag = self.findShotExporterTag(trackItem)
      if tag:
        try:
          newTrack = self._findTrackByUID(sequence, tag.metadata()["tag.track"])
          if newTrack:
            self._trackName = newTrack.name()
            foundTrackName = True
          break
        except:
          pass

    return foundTrackName

  def _handleMismatchedTracks(self, selectedItems, sequence, project):
    foundMismatch = False
    targetTrackNames = set()
    targetTrackNames.add(self._trackName)
    for trackItem in selectedItems:
      tag = self.findShotExporterTag(trackItem)
      if tag:
        try:
          newTrack = self._findTrackByUID(sequence, tag.metadata()["tag.track"])
          if self._trackName != newTrack.name():
            targetTrackNames.add(newTrack.name())
            foundMismatch = True
        except:
          foundMismatch = True

    # confirm that all of the track items are supposed to generate to the same track
    if foundMismatch:
      # if it's a restricted project, just fail, because we can't generate to the same track, which is what will happen
      if project.isRestricted():
        QtWidgets.QMessageBox.critical(hiero.ui.mainWindow(), "HieroPlayer", "The selected track items have tags that apply to different target tracks. Please re-build the external media track for the selected track items (in Hiero), save the project, and try again.")
        return False
      elif len(targetTrackNames) > 1:
        # if there's only one item, that will get used and everything will generate there
        # if there's multiple, then let the user pick which one or cancel
        selectedTrackName = self._selectTrackName(targetTrackNames)
        if not selectedTrackName:
          return False

        self._trackName = selectedTrackName

    return True

  def createTrackItemCollisionDialog(self, srcCollisions, track, uniqueTrackName):
    labelText = "There are existing track items on the '%s' track that would be overwritten by this operation. What would you like to do?\n" % (track.name())
    dialog = TrackItemCollisionDialog(len(srcCollisions), track, uniqueTrackName, labelText=labelText, enableDeleteButton=False, enableRefreshButton=False)
    dialog.setWindowTitle("Create Comp")
    return dialog


  def doit(self):
    if not self._trackItems:
      return

    project = self._trackItems[0].project()
    try:
      self._doit()

    except ValueError as e:
      self._success = False
      InvalidOutputResolutionMessage(str(e))
    except Exception as e:
      self._success = False
      self._errorHandler.error(str(e))
      
    # This code disabled because it could lead to rolling back the *previous* create comp if the user cancelled this one or there was an error.
    # Making this work properly relies on fixing 'Bug 29363 - Sequences of straightforward operations via Python API fail when in Undo group'

    #if not self._success:
      # Try to roll back all the undos.  We should be able to wrap everything in a single undo block, but that doesn't work, see Bug 29363.
      # This might cause problems if the last thing the user did before Create Comp was to add a tag, but that seems unlikely, and leaving all
      # the export tags when 'Create Comp' fails is really annoying.
    #  while project.undoItemText() in ("Create Comp", "Add Tag"):
    #    project.undo()


  def _doit(self):
    self.execute(self)



  def execute(self, singleNukeScript = None, singleNukeScriptMasterTrackItem = None):
    """ This function was created to set the master trackItem in popup dialog
    created in gui when creating comp out of multiple track items
    """

    # find the first trackItem's sequence and it's project
    track = self._trackItems[0].parent()
    sequence = track.parent()
    project = sequence.project()

    # If the user hasn't set a root directory return
    if not hiero.ui.getProjectRootInteractive(project):
      return

    # Check if there's a valid project shot preset.  If not, return.
    self.shotPreset = self.getExportPreset(project)

    if not self.shotPreset:
      return

    # Check that the preset render output is supported.  At the moment, we can't deal with rendering to mov etc.
    if not checkPresetRenderOutput(self.shotPreset):
      return


    # Warn the user if they're trying to open multiple track items since each one will start a new Nuke instance
    if len(self._trackItems) > 1 and not hiero.core.isHieroPlayer():

      if (singleNukeScriptMasterTrackItem==None):
        needsDialog = True
      else:
        needsDialog = False
        self._singleNukeScript = singleNukeScript

      if needsDialog == True:
        dialog = CreateCompForTrackItemsDialog(self._trackItems, self.shotPreset, parent=hiero.ui.mainWindow())
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
          self._singleNukeScript = not dialog.multipleComps()
          singleNukeScriptMasterTrackItem = dialog.masterTrackItem()
          self.shotPreset = dialog.preset()

        else:
          # Cancelled
          return

    else:
      self._singleNukeScript = False
      singleNukeScriptMasterTrackItem = None

    if self._singleNukeScript:
      ######
      # Build one script for all track items
      ######

      try:
        trackItemData = self._preProcessTrackItems([singleNukeScriptMasterTrackItem])

        self._showProgress()

        if trackItemData:
          singleNukeScriptMasterTrackItem, tag, version = trackItemData[0]

          self._exportSequence(self._trackItems, singleNukeScriptMasterTrackItem,
                               version, self._effectItems, self._annotations, project)

          with project.beginUndo("Create Comp"):
            self._processExportedTrackItems(trackItemData, sequence, project)
      finally:
        self._progressTask = None

    else:
      ######
      # Export all the track items individually.  If the items are already tagged a new script version will be created,
      # and they won't be returned here since they already have an item for the comp.
      ######

      try:
        trackItemData = self._preProcessTrackItems(self._trackItems)

        self._showProgress()

        if trackItemData:
          trackItemsToBuildFrom = self._exportShots(trackItemData, self._effectItems, self._annotations, project)

          with project.beginUndo("Create Comp"):
            self._processExportedTrackItems(trackItemData, sequence, project)

      finally:
        self._progressTask = None
    

  def getExportPreset(self):
    """ Get the export preset to be used as the basis for creating the comp.  To be implemented by sub-classes. """
    raise NotImplementedError

class CreateCompAction(CreateCompActionBase):
  """ Action for Create Comp.  Uses the project shot preset for export. """

  def __init__(self, trackItems, effectItems, annotations, title="Create Comp"):
    super(CreateCompAction, self).__init__(trackItems, effectItems, annotations, title)


  def getExportPreset(self, project):
    return getProjectShotPreset(project)



class CreateCompSpecialAction(CreateCompActionBase):
  """ Action for Create Comp Special.  Shows the export dialog for the user to choose and configure their preset. """

  def __init__(self, trackItems, effectItems, annotations, title="Create Comp Special.."):
    super(CreateCompSpecialAction, self).__init__(trackItems, effectItems, annotations, title)


  def getExportPreset(self, project):
    preset = showCreateCompSpecialDialog(self._trackItems)
    return preset

