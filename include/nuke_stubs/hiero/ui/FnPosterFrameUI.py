# -*- coding: utf-8 -*-

import itertools
import functools
import hiero.core
from hiero.core import Project
from hiero.core.events import EventType
import hiero.ui
from PySide2.QtGui import QIcon, QIntValidator
from PySide2.QtWidgets import (QComboBox,
                               QDialog,
                               QDialogButtonBox,
                               QGridLayout,
                               QLabel,
                               QLineEdit,
                               QMenu,
                               QVBoxLayout,
                               QWidget)

"""
UI code for setting poster frames on clips in the bin. Registers a context menu
event listener and adds entries to it.
"""


def findIntersectingFrameRange(ranges):
  """ Try to find the intersection of a sequence of frame range tuples. Raises a
  RuntimeError if the ranges did not all intersect.
  """
  istart, iend = ranges[0]
  for start, end in itertools.islice(ranges, 1, None):
    if start > iend or end < istart:
      raise RuntimeError("Ranges don't intersect")
    else:
      istart = max(start, istart)
      iend = min(end, iend)
  return istart, iend


class PosterFrameSelectionWidgets(object):
  """ Not a widget itself, creates and manages the label and input widget for
  selecting poster frame numbers.
  """
  def __init__(self, label):
    self._label = label
    self._labelWidget = QLabel(label)
    self._lineEdit = QLineEdit()

  def labelWidget(self):
    return self._labelWidget

  def inputWidget(self):
    return self._lineEdit

  def setEnabled(self, enabled):
    self._labelWidget.setEnabled(enabled)
    self._lineEdit.setEnabled(enabled)

  def setRange(self, minFrame, maxFrame, startFrame):
    # Update the label to include the available frame range
    self._labelWidget.setText( self._label + " (%d-%d)" % (minFrame, maxFrame) )

    # Set the line edit value and create a validator for the available range
    self._lineEdit.setText( str(startFrame) )
    validator = QIntValidator(minFrame, maxFrame, self._lineEdit)
    self._lineEdit.setValidator(validator)

  def value(self):
    return int(self._lineEdit.text())


class PosterFrameDialog(QDialog):
  """ Dialog for setting custom poster frames on selected clips. """

  # Flags for the selected mode, which should match the indexes in the combo box
  kAbsolute = 0
  kRelative = 1

  def __init__(self, clips, parent):
    QDialog.__init__(self, parent)
    self._clips = clips
    self.setWindowTitle("Set Poster Frame")

    layout = QVBoxLayout()
    self.setLayout(layout)

    self._comboBox = QComboBox()
    layout.addWidget(self._comboBox)
    self._comboBox.addItems( ["Absolute", "Relative"] )
    self._comboBox.currentIndexChanged.connect(self.onComboBoxIndexChanged)

    gridLayout = QGridLayout()
    gridLayout.setSpacing(5)
    layout.addLayout(gridLayout)

    # Create the widgets for setting the absolute frame number (that is, the
    # frame within the media rather than treating the first frame of the clip as 0)
    self._absoluteWidgets = PosterFrameSelectionWidgets("FrameNumber")
    gridLayout.addWidget(self._absoluteWidgets.labelWidget(), 0, 0)
    gridLayout.addWidget(self._absoluteWidgets.inputWidget(), 0, 1)
    try:
      # Determine the available ranges. If the selected clips don't overlap an exception
      # will be thrown, in which case this option is disabled.
      clipAbsRanges = [ (clip.sourceIn(), clip.sourceIn()+clip.duration()-1) for clip in clips ]
      availableAbsRange = findIntersectingFrameRange(clipAbsRanges)
      startFrame = availableAbsRange[0]
      if len(clips) == 1:
        startFrame = clips[0].posterFrame() + clips[0].sourceIn()
      self._absoluteWidgets.setRange(availableAbsRange[0], availableAbsRange[1], startFrame)
    except:
      availableAbsRange = None

    # Create the widgets for setting the relative frame number, i.e. starting at
    # 0 for all clips. The range is restricted to the length of the shortest
    # selected clip
    maxFrame = min( (clip.duration() for clip in clips) ) - 1
    self._relativeWidgets = PosterFrameSelectionWidgets("Frame Offset")
    startFrame = 0
    if len(clips) == 1:
      startFrame = clips[0].posterFrame()
    self._relativeWidgets.setRange(0, maxFrame, startFrame)
    gridLayout.addWidget(self._relativeWidgets.labelWidget(), 1, 0)
    gridLayout.addWidget(self._relativeWidgets.inputWidget(), 1, 1)

    # Add the Ok and Cancel buttons
    buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttonBox.accepted.connect(self.accept)
    buttonBox.rejected.connect(self.reject)
    layout.addWidget( buttonBox )

    # Set the default to relative
    self._comboBox.setCurrentIndex(PosterFrameDialog.kRelative)

    # If there's no valid range for the absolute setting, disable the combo box
    self._comboBox.setEnabled(availableAbsRange is not None)

  def accept(self):
    # Set the absolute or relative poster frame values on each clip
    if self._comboBox.currentIndex() == PosterFrameDialog.kAbsolute:
      posterFrameFunc = lambda clip: self._absoluteWidgets.value() - clip.sourceIn()
    else:
      posterFrameFunc = lambda clip: self._relativeWidgets.value()
    setPosterFrames(self._clips, posterFrameFunc)

    QDialog.accept(self)

  def onComboBoxIndexChanged(self, index):
    self._absoluteWidgets.setEnabled(index == PosterFrameDialog.kAbsolute)
    self._relativeWidgets.setEnabled(index == PosterFrameDialog.kRelative)


def showPosterFrameDialog(clips):
  dialog = PosterFrameDialog(clips, hiero.ui.mainWindow())
  dialog.exec_()


def setPosterFrames(clips, func):
  """ For each clip, set the poster frame, calling func to get the value """
  project = clips[0].project()
  with project.beginUndo("Set Poster Frame"):
    for clip in clips:
      clip.setPosterFrame( func(clip) )


def findClipsInBinSelection(selection):
  """ Find selected clips, recursing through the bin hierarchy. """
  clips = []
  for item in selection:
    if isinstance(item, hiero.core.Bin):
      clips.extend( findClipsInBinSelection(list(item.items())) )
    elif isinstance(item, hiero.core.BinItem) and isinstance(item.activeItem(), hiero.core.Clip):
      clips.append( item.activeItem() )
  return clips


def isValidClipForPosterFrames(clip):
  """ Check if poster frames can be set on a clip. """
  return clip.duration() > 1 and clip.mediaSource().hasVideo()


ClipPosterFrameFuncs = {
  Project.PosterFrameSetting.eFirst : lambda clip: 0,
  Project.PosterFrameSetting.eMiddle : lambda clip: (clip.duration() - 1) // 2,
  Project.PosterFrameSetting.eLast : lambda clip: clip.duration() - 1
}

def binContextMenuEvent(event):
  """ Callback when context menu is shown in the project panel. """

  # Only want to change the poster frame for clips. Find any selected, and make
  # sure they have video and duration > 1
  clips = findClipsInBinSelection(event.sender.selection())
  clips = [clip for clip in clips if isValidClipForPosterFrames(clip)]
  if not clips:
    return

  # Add a sub-menu, under which are the poster frame options
  menu = event.menu
  posterFrameMenu = QMenu("Set Poster Frame")
  try:
    # Find the localization menu and insert before it
    localizationMenuAction = next(action for action in menu.actions() if action.text() == "Localization Policy")
    menu.insertMenu(localizationMenuAction, posterFrameMenu)
  except:
    # Fall back to adding at the end if the localization menu wasn't found
    menu.addMenu(posterFrameMenu)

  tickIconGrey = QIcon( "icons:Ticked_Grey.png" )
  tickIconOrange = QIcon( "icons:Ticked.png" )

  # Keep track of the clips which have first/middle/last currently set to determine
  # whether the custom action is ticked
  nonCustomClips = set()

  # Create the first/middle/last actions
  actionData = ( ("First", ClipPosterFrameFuncs[Project.PosterFrameSetting.eFirst]),
                 ("Middle", ClipPosterFrameFuncs[Project.PosterFrameSetting.eMiddle]),
                 ("Last", ClipPosterFrameFuncs[Project.PosterFrameSetting.eLast]) )
  for text, posterFrameFunc in actionData:
    action = posterFrameMenu.addAction(text)

    # Set an orange tick if all selected clips match the selection, and a grey one
    # if some do
    matchingClips = [clip for clip in clips if clip.posterFrame() == posterFrameFunc(clip)]
    nonCustomClips.update(matchingClips)
    if len(matchingClips) == len(clips):
      action.setIcon(tickIconOrange)
    elif len(matchingClips) > 0:
      action.setIcon(tickIconGrey)

    action.triggered.connect(functools.partial(setPosterFrames, clips, posterFrameFunc))

  # Add the custom action which shows the dialog, and set the tick icon on it if needed
  customAction = posterFrameMenu.addAction("Custom...")
  customAction.triggered.connect(lambda: showPosterFrameDialog(clips))
  if len(nonCustomClips) == 0:
    customAction.setIcon(tickIconOrange)
  elif len(nonCustomClips) < len(clips):
    customAction.setIcon(tickIconGrey)


def viewerContextMenuEvent(event):
  """ Callback when context menu is shown in a viewer. """
  viewer = event.sender

  # Can only set poster frames for clips
  sequence = viewer.player().sequence()
  if not isinstance(sequence, hiero.core.Clip) or not isValidClipForPosterFrames(sequence):
    return

  # Add menu entry which will set the clip poster frame to the viewer's current frame
  menu = event.menu
  action = menu.addAction("Set Poster Frame")
  action.triggered.connect( lambda: sequence.setPosterFrame(viewer.time()) )


# Register the context menu event callbacks
eventFlags = (EventType.kShowContextMenu, EventType.kBin)
hiero.core.events.registerInterest(eventFlags,
                                   binContextMenuEvent)
eventFlags = (EventType.kShowContextMenu, EventType.kViewer)
hiero.core.events.registerInterest(eventFlags,
                                   viewerContextMenuEvent)


def onClipAddedToProject(event):
  """ Callback when a clip is added to a project. Sets the poster frame according
  to the project settings.
  """
  clip = event.clip
  project = clip.project()
  mode, customFrame = project.posterFrameSettings()
  if mode == Project.PosterFrameSetting.eCustom:
    clip.setPosterFrame(customFrame)
  else:
    clip.setPosterFrame(ClipPosterFrameFuncs[mode](clip))

hiero.core.events.registerInterest(EventType.kClipAdded, onClipAddedToProject)
