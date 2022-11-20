# ScanForVersions is the action responsible for scanning for versions.
# This action is added to the BinView context menu.
# The code responsible for the scanning is located in hiero.core.VersionScanner
#
# This file also contains several helper functions for scanning versions when
# the user does version up/down/etc in the UI.  These are called from C++ code

import hiero.core
import hiero.core.log
import hiero.core.VersionScanner
import hiero.ui
from PySide2 import (QtCore, QtGui, QtWidgets)

import foundry.ui
import threading
import time



class ScanForVersionsTask(object):
  def __init__(self):
    self._task = foundry.ui.ProgressTask("Finding Versions...")


  def scanForVersions(self, versions, postScanFunc, shouldDisplayResults):
    """ Scan a list of versions for new versions.  If postScanFunc is provided,
    this will be called after the scan.
    Returns True if scanning was completed, or False if the user cancelled or
    an error occurred.
    """
    try:
      self.scanForVersionsInternal(versions, postScanFunc, shouldDisplayResults)
      return True
    except StopIteration: # This is raised if the user cancelled
      return False
    except: # For other exceptions, log them and return False
      hiero.core.log.exception("Scan for Versions failed")
      return False


  def scanForVersionsInternal(self, versions, postScanFunc, shouldDisplayResults):
    scanner = hiero.core.VersionScanner.VersionScanner()

    for version in versions:
      self.rescanClipRanges(version)
      self.processEventsAndCheckCancelled()

    # Find all the files to be added as versions
    numNewFiles = 0
    newVersionFiles = []
    newVersions = []

    # For each version find the additional files
    for version in versions:
      newFiles = scanner.findVersionFiles(version)
      newVersionFiles.append ( [ version, newFiles ] )
      numNewFiles += len(newFiles)
      self.processEventsAndCheckCancelled()

    # Now create the clips for the additional files
    fileIndex = 0
    for versionFile in newVersionFiles:

      version, newFiles = versionFile

      for newFile in newFiles:
        self.processEventsAndCheckCancelled()

        fileIndex += 1
        self._task.setProgress(int(100.0*(float(fileIndex)/float(numNewFiles))))

        newVersion = scanner.createAndInsertClipVersion(version.parent(), newFile)
        if newVersion:
          newVersions.append(newVersion)

      # If we have a post scan function then run it (version up/down, min/max)
      if (postScanFunc is not None):
        oldClip = version.item()
        postScanFunc()
        binitem = version.parent()
        newClip = binitem.activeVersion().item()

        # Then update any viewers looking at the old clip to the new clip
        hiero.ui.updateViewer(oldClip, newClip)

    # If we're supposed to display results then do so
    if (shouldDisplayResults):
      self.displayResults(len(newVersions))


  def processEventsAndCheckCancelled(self):
    """ Call QCoreApplication.processEvents() and check if the user has cancelled
    the progress task.  If cancelled, StopIteration will be raised.
    """
    QtCore.QCoreApplication.processEvents()
    if self._task.isCancelled():
      raise StopIteration()


  def displayResults(self, numNewVersions):
    """ Display results """
    msgBox = QtWidgets.QMessageBox()
    msgBox.setText("Found " + str(numNewVersions) + " new versions")
    msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
    msgBox.exec_()


  def rescanClipRanges(self, activeVersion):
    """ From an active version, iterates through all the siblings inside the BinItem """
    binItem = activeVersion.parent()
    if binItem:
      for version in list(binItem.items()):
        clip = version.item()
        if clip:
          clip.rescan()


def ScanAndNextVersion(version):
  '''Scan then move to next version'''
  binitem = version.parent()
  _DoScanForVersions([version], binitem.nextVersion, False)

def ScanAndPrevVersion(version):
  ''' Scan then move to prev version'''
  binitem = version.parent()
  _DoScanForVersions([version], binitem.prevVersion, False)

def ScanAndMinVersion(version):
  '''Scan then move to min version'''
  binitem = version.parent()
  _DoScanForVersions([version], binitem.minVersion, False)

def ScanAndMaxVersion(version):
  '''Scan then move to max version'''
  binitem = version.parent()
  _DoScanForVersions([version], binitem.maxVersion, False)


def ScanVersionsAndCallbackTrackItems(trackItems, callback):
  """ Helper function for track items version changes.  Does the scan and
  calls callback on each item.
  """
  # Build a set of versions so we're not scanning the same version multiple times
  versionsToScan = set()
  for item in trackItems:
    versionsToScan.add(item.currentVersion())

  # Do the scan
  ok = _DoScanForVersions(versionsToScan, None, False)

  # If the scan was successful, do the callback on each item
  if ok:
    for item in trackItems:
      callback(item)
  return ok


def ScanAndNextVersionTrackItems(trackItems):
  '''Scan then move to next version on the track items'''
  return ScanVersionsAndCallbackTrackItems(trackItems, hiero.core.TrackItem.nextVersion)


def ScanAndPrevVersionTrackItems(trackItems):
  '''Scan then move to next version on the track items'''
  return ScanVersionsAndCallbackTrackItems(trackItems, hiero.core.TrackItem.prevVersion)


def ScanAndMaxVersionTrackItems(trackItems):
  '''Scan then move to next version on the track items'''
  return ScanVersionsAndCallbackTrackItems(trackItems, hiero.core.TrackItem.maxVersion)


def ScanAndMinVersionTrackItems(trackItems):
  '''Scan then move to next version on the track items'''
  return ScanVersionsAndCallbackTrackItems(trackItems, hiero.core.TrackItem.minVersion)


def _DoScanForVersions(versions, postUpdateFunc, shouldDisplayResults):
  """ Do the version scan.   Creates a ScanForVersionsTask and executes it on
  the main thread,
  """
  scanner = ScanForVersionsTask()
  return scanner.scanForVersions(versions, postUpdateFunc, shouldDisplayResults)


# Action to scan for new versions
class ScanForVersionsAction(QtWidgets.QAction):

  _scanner = hiero.core.VersionScanner.VersionScanner()

  def __init__(self):
      QtWidgets.QAction.__init__(self, "Scan For Versions", None)
      self.triggered.connect(self.doit)
      hiero.core.events.registerInterest((hiero.core.events.EventType.kShowContextMenu, hiero.core.events.EventType.kBin), self.eventHandler)
      hiero.core.events.registerInterest((hiero.core.events.EventType.kShowContextMenu, hiero.core.events.EventType.kTimeline), self.eventHandler)
      hiero.core.events.registerInterest((hiero.core.events.EventType.kShowContextMenu, hiero.core.events.EventType.kSpreadsheet), self.eventHandler)


  def doit(self):
    # get the currently selected versions from UI
    versions = self.selectedVersions()

    if len(versions) == 0:
      hiero.core.log.info( "No valid versions found in selection" )
      return

    # For each version, do:
    # - rescan any versions already loaded to find the maximum available range
    # - run _scanner.doScan which returns added versions
    # - compute the total count of new versions.
    _DoScanForVersions(versions, None, True)

  def eventHandler(self, event):

    enabled = False
    if hasattr(event.sender, 'selection'):
      s = event.sender.selection()
      if len(s)>=1:
        enabled = True
      
      # enable/disable the action each time
      if enabled:
        for a in event.menu.actions():
          if a.text().lower().strip() == "version":
            if self._menuActionsAreEnabled(a.menu()):
              hiero.ui.insertMenuAction( self, a.menu(), before="foundry.project.versionup" ) # Insert after 'Version' sub-menu
              break

  def _menuActionsAreEnabled(self, versionMenu):
      """Check if actions in versionMenu are enabled to add this action"""
      versionActions = versionMenu.actions()
      enabledActions = [ action for action in versionActions if action.isEnabled() ]
      return len(enabledActions) > 0

  # Get all selected active versions
  def selectedVersions(self):
    selection = hiero.ui.currentContextMenuView().selection()
    versions = []
    self.findActiveVersions(selection, versions)
    return (versions)

  #
  def alreadyHaveVersion(self, findversion, versions):
    newFilename = findversion.item().mediaSource().fileinfos()[0].filename()
    for version in versions:
      thisFilename = version.item().mediaSource().fileinfos()[0].filename()
      if (newFilename == thisFilename):
        return True

    return False

  # Find all active versions in container and append to versions
  def findActiveVersions(self, container, versions):
    # Iterate through selection
    if isinstance(container, (list,tuple)):
      for i in container:
        self.findActiveVersions(i, versions)
    # Dive into Projects to find clipsBin (NB: not strictly needed at the moment, we get RootBins from BinView)
    elif isinstance(container, hiero.core.Project):
      self.findActiveVersions(container.clipsBin(), versions)
    # Dive into Bins to find BinItems
    elif isinstance(container, hiero.core.Bin):
      for i in list(container.items()):
        self.findActiveVersions(i, versions)
    elif isinstance(container, hiero.core.TrackItem) and isinstance(container.source(), hiero.core.Clip):
      activeVersion = container.currentVersion()
      if activeVersion and not activeVersion.isNull():
        if not self.alreadyHaveVersion(activeVersion, versions):
        #if activeVersion not in versions:
          versions.append(activeVersion)
    # Dive into BinItem to retrieve active Version
    elif isinstance(container, hiero.core.BinItem) and isinstance(container.activeItem(), hiero.core.Clip):
      activeVersion = container.activeVersion()
      if activeVersion:
        if not self.alreadyHaveVersion(activeVersion, versions):
        #if activeVersion not in versions:
          versions.append(activeVersion)

# Instantiate the action to get it to register itself.
action = ScanForVersionsAction()

