"""
Code for handling changes in the localization default in the preferences
and applying that as knob defaults on Read nodes.
"""

import nuke
from PySide2.QtCore import QTimer


# Name of the localisation policy prefs knob
kLocalizationPolicyDefaultKnob = "LocalizationPolicyDefault"


def updateReadKnobLocalisationDefaults(value):
  """ Set the knob defaults for the nodes with the cacheLocal knob. """
  nuke.knobDefault("localizationPolicy", value)


def onPrefsKnobChanged():
  """ Callback from the preferences node.  If the default localisation 
  policy has changed, update it on the read nodes.
  """
  knob = nuke.thisKnob()
  if knob.name() == kLocalizationPolicyDefaultKnob:
    updateReadKnobLocalisationDefaults(knob.value())


def initCallbacks():
  """ Get the default localisation policy from the preferences node and set
  up the knob changed callback.
  """
  prefsNode = nuke.toNode("preferences")
  knob = prefsNode.knob(kLocalizationPolicyDefaultKnob)
  updateReadKnobLocalisationDefaults(knob.value())
  nuke.addKnobChanged(onPrefsKnobChanged, node=prefsNode)


# This script is imported before the prefs node is loaded.  To ensure we get
# the correct initial value for the localisation policy, use a QTimer to defer
# initialisation.  initCallbacks will be called once the Qt event loop is
# running.
QTimer.singleShot(0, initCallbacks)
