# Shows how to use the Playback Started/Stopped events and adds a simple message to the MainWindow Status Bar.

import hiero.ui
import hiero.core.events

def updateStatusBarMessage(event):
  bar = hiero.ui.mainWindow().statusBar()
  bar.showMessage('Playback Event: ' + str(event.type), timeout = 3000)

# Register the kPlaybackStarted / kPlaybackStopped events
hiero.core.events.registerInterest('kPlaybackStarted',updateStatusBarMessage)
hiero.core.events.registerInterest('kPlaybackStopped',updateStatusBarMessage)