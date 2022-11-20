import itertools
import hiero.core
from PySide2 import (QtCore, QtGui, QtWidgets)


class _TrackViewKeyPressRedirect(QtCore.QObject):
  """ Event filter to catch Space being pressed on the tracks list view. """

  def __init__(self, parent=None):
    QtCore.QObject.__init__(self, parent)

  def eventFilter(self, obj, event):
    # Grab the space key event and use it to toggle multiple selections
    if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key(QtCore.Qt.Key_Space):
      current = obj.currentIndex().model().itemFromIndex(obj.currentIndex())
      if current.checkState() == QtCore.Qt.Checked:
        current.setCheckState(QtCore.Qt.Unchecked)
      else:
        current.setCheckState(QtCore.Qt.Checked)
      for index in obj.selectedIndexes():
        selectedItem = index.model().itemFromIndex(index)
        if selectedItem.checkState() == QtCore.Qt.Checked:
          selectedItem.setCheckState(QtCore.Qt.Unchecked)
        else:
          selectedItem.setCheckState(QtCore.Qt.Checked)
      return QtCore.QObject.eventFilter(self, obj, event)
    else:
      # If not the space key then back to standard event processing
      return QtCore.QObject.eventFilter(self, obj, event)


class TrackSelectionWidget(QtWidgets.QWidget):
  """ Widget for selecting tracks for export.  Note that the way this is configured on the preset
      is slightly odd.  The excluded tracks are stored in the session by name, but for determining
      which tracks are actually excluded we use their guids.  This allows for the same selection to
      be used for different sequences, but means things can get a bit confused if there are multiple
      tracks with the same name. """

  def __init__(self, sequences, excludedTrackNames, excludedTrackIDs, parent=None):
    QtWidgets.QWidget.__init__(self, parent)

    # Build the UI

    layout = QtWidgets.QVBoxLayout()
    layout.setContentsMargins(0,0,0,0)
    self.setLayout(layout)

    label = QtWidgets.QLabel("Tracks for this export:", self)
    layout.addWidget(label)

    self._sequences = sequences
    self._excludedTrackNames = excludedTrackNames
    self._excludedTrackIDs = excludedTrackIDs

    allSelected = (len(excludedTrackNames) == 0)

    self._trackListModel = QtGui.QStandardItemModel()

    self._trackListView = QtWidgets.QListView()
    keyPressRedirect = _TrackViewKeyPressRedirect(self)
    self._trackListView.installEventFilter(keyPressRedirect)
    self._trackListView.setModel(self._trackListModel)

    layout.addWidget(self._trackListView)

    self._allTracksModelItem = QtGui.QStandardItem('all tracks')
    allTracksItemFont = self.font()
    allTracksItemFont.setItalic(True)
    self._allTracksModelItem.setFont(allTracksItemFont)
    self._allTracksModelItem.setCheckable(True)
    if allSelected:
      self._allTracksModelItem.setCheckState(QtCore.Qt.Checked)
    self._trackListModel.appendRow(self._allTracksModelItem)

    self._trackModelItems = []

    self._tracks = []
    for sequence in self._sequences:
      self._tracks.extend( reversed(sequence.videoTracks()) )
      self._tracks.extend( reversed(sequence.audioTracks()) )

    excludedTracks = []
    for sequence in self._sequences:
      excludedTracks.extend( [track for track in itertools.chain(sequence.videoTracks(), sequence.audioTracks()) if track.name() in excludedTrackNames ] )

    for track in self._tracks:
      item = QtGui.QStandardItem(track.name())
      item.setData(track.guid())
      item.setIcon(self.getIconForTrack(track))

      # If a track contains offline items we change the track icon to show a warning
      # and then change the tooltip to show a quick list of offline items
      offlineItems = self.offlineTrackItems(track)
      if offlineItems:
        if isinstance(track,hiero.core.AudioTrack):
          item.setIcon(QtGui.QIcon("icons:AudioOnlyWarning.png"))
        if isinstance(track,hiero.core.VideoTrack):
          item.setIcon(QtGui.QIcon("icons:VideoOnlyWarning.png"))
        item.setText(item.text() + "  ( Media Offline )")
        item.setToolTip("Offline Items will be ignored:\n" + '\n'.join(offlineItems))

      # If tracks are disabled or empty we disable the checkbox and change
      # the tooltip to inform the user why they are disabled
      trackNotValid = False
      if not track.isEnabled():
        item.setToolTip("Track is Disabled")
        trackNotValid = True

      if not self.trackHasTrackOrSubTrackItems(track):
        item.setToolTip("Track is Empty")
        trackNotValid = True

      if trackNotValid:
        if track not in excludedTracks:
          excludedTracks.append(track)
          excludedTrackNames.append(track.name())
        if track.guid() not in excludedTrackIDs:
          excludedTrackIDs.append(track.guid())

      if track in excludedTracks:
        item.setCheckState(QtCore.Qt.Unchecked)
        if trackNotValid:
          item.setEnabled(False)
        else:
          item.setEnabled(True)
      else:
        if not allSelected:
          item.setCheckState(QtCore.Qt.Checked)
        item.setEnabled(True)

      item.setCheckable(True)
      item.setEditable(False)
      self._trackListModel.appendRow(item)
      self._trackModelItems.append(item)

      self._trackListModel.itemChanged.connect(self.onItemChanged)
      self._inOnItemChanged = False


  def getIconForTrack(self, track):
    """ Get the icon to use for a track. """
    trackIcon = None
    if isinstance(track,hiero.core.AudioTrack):
      trackIcon = QtGui.QIcon("icons:AudioOnly.png")
    elif isinstance(track,hiero.core.VideoTrack):
      trackIcon = QtGui.QIcon("icons:VideoOnly.png")
    return trackIcon


  def trackHasTrackOrSubTrackItems(self, track):
    """ Test if a track has any items or sub-track items. """
    if (
      len(list(track.items())) > 0 or
      (isinstance(track, hiero.core.VideoTrack) and len( [ item for item in itertools.chain(*track.subTrackItems()) ] ) > 0)
      ):
      return True
    else:
      return False


  def offlineTrackItems(self, track):
    """ Get a list offline track items for a track. """
    offlineMedia = []
    for trackitem in track:
      if not trackitem.isMediaPresent():
        try:
            sourcepath = trackitem.source().mediaSource().fileinfos()[0].filename()
        except:
            sourcepath = "Unknown Source"
        offlineMedia.append(' : '.join([trackitem.name(), sourcepath]))
    return offlineMedia


  def onItemChanged(self, item):
    """ Handle the user checking/unchecking an item in the list. """

    # Prevent recursion
    if self._inOnItemChanged:
      return
    self._inOnItemChanged = True

    # If the user clicked the 'all tracks' option, uncheck everything else
    if item is self._allTracksModelItem:
      for trackItem in self._trackModelItems:
        trackItem.setCheckState(QtCore.Qt.Unchecked)

    # Otherwise a single track was changed
    else:
      self._allTracksModelItem.setCheckState(QtCore.Qt.Unchecked)

    # Clear the exclusion lists
    del self._excludedTrackNames[:]
    del self._excludedTrackIDs[:]

    # If 'all tracks' isn't selected, check the state of each track item.
    # else check for rendering all non-disabled tracks
    if self._allTracksModelItem.checkState() == QtCore.Qt.Unchecked:

      for item in self._trackModelItems:
        if item.checkState() == QtCore.Qt.Unchecked:
          track = self.findTrackByGuid(item.data())

          self._excludedTrackNames.append(track.name())
          self._excludedTrackIDs.append(track.guid())
    else:
      for item in self._trackModelItems:
        track = self.findTrackByGuid(item.data())
        if not track.isEnabled():
          self._excludedTrackNames.append(track.name())
          self._excludedTrackIDs.append(track.guid())

    self._inOnItemChanged = False


  def findTrackByGuid(self, guid):
    """ Find a track in the list with the given GUID. """
    for track in self._tracks:
      if track.guid() == guid:
        return track
    return None
