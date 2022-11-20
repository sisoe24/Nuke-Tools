# Copyright (c) 2020 The Foundry Visionmongers Ltd.  All Rights Reserved.

import PySide2.QtWidgets as QtWidgets

from hiero.core.FnFloatRange import IntRange, FloatRange

from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.ui.FnUIProperty import UIPropertyFactory

from . FnDisclosureButton import DisclosureButton

import nuke_internal as nuke

class NodePropertyWidget(QtWidgets.QWidget):
  """ This class generates a widget based on the passed in node. The created
  widget contains property widgets for all the knobs that are present in the
  propertyDictionaries passed into the constructor. The type of widget created
  and its initial value is based on the value(s)from the corresponding knobs on
  the node. This class will also update the values of the knob in the node when
  setting a value on a property widget. It will also subsequently update the
  remaining property widgets based on the state of their corresponding knobs, as
  a change to one knob can result in changes to the state of other knobs - this
  is done so that we don't have to duplicate the knob interaction logic for the
  property widgets but instead get that logic directly from the node. The layout
  of the property widgets will attempt to mimic the layout of the knobs on the
  node. Note: the node must not be deleted until after the NodePropertyWidget
  has been deleted."""

  # Knob flags that aren't exposed in the nuke Python API
  KNOB_CHANGED_ALWAYS = 0x0000000000010000
  SAVE_MENU = 0x0000000002000000
  SLIDER = 0x0000000000000002
  STORE_INTEGER = 0x0000000000000008

  def __init__(self, node, propertyDictionaries, presetDictionary):
    QtWidgets.QWidget.__init__(self)
    self._node = node
    self._presetDictionary = presetDictionary
    self._knobs = []
    self._layout = TaskUIFormLayout()
    self.initializeUI(propertyDictionaries)
    self.setLayout(self._layout)
    self.updateProperties()

  def createProperty(self, label, key, values, tooltip, isVisible, isEnabled):
    """Creates a 'UIProperty' widget using the passed in label, preset key, values and tooltip which
    will store any changes to its value in the _presetDictionary at the given key. Will also
    connect the property with the propertyUpdated callback and append a tuple of the key and property
    widget to the _knobs list."""
    propertyWidget = UIPropertyFactory.create(type(values), key=key, value=values, dictionary=self._presetDictionary, label=label, tooltip=tooltip)
    propertyWidget.setEnabled(isEnabled)
    propertyWidget.update(commit=True)
    self.connectProperty(propertyWidget)
    self._knobs.append((key, propertyWidget))
    return propertyWidget

  def createPropertyFromKnob(self, knob):
    """ Creates a 'UIProperty' widget based on the values from the knob
    which is retrieved using the knobName specified. See createProperty
    for details on the UIProperty."""
    knobName = knob.name()

    if isinstance(knob, nuke.Enumeration_Knob):
      # If the Enumeration_Knob has the SAVE_MENU flag set then calling value()
      # will return the current index and a list of all available entries as a
      # string. This is because nk_enumeration_knob_value just calls
      # Enumeration_Knob::to_script() which checks for the SAVE_MENU flag.
      # We always want knob.value() to return the current value only so we clear
      # the SAVE_MENU flag.
      knob.clearFlag(self.SAVE_MENU)
      values = self.enumKnobValues(knob)
    elif knob.getFlag(self.SLIDER):
      if knob.getFlag(self.STORE_INTEGER):
        values = IntRange(int(knob.min()), int(knob.max()), int(knob.value()))
      else:
        values = FloatRange(knob.min(), knob.max(), knob.value())
    else:
      if knob.getFlag(self.STORE_INTEGER):
        values = int(knob.value())
      else:
        values = knob.value()

    # This sets the KNOB_CHANGED_ALWAYS flag, this is because the node's
    # knob_changed callback is not normally called if the node panel is not
    # visible unless this flag is set. We need the knob_changed callbacks to
    # be called so that we know how changing one knob changes the other knobs.
    knob.setFlag(self.KNOB_CHANGED_ALWAYS)

    # update knob if preset has a value, otherwise set preset to knob value
    if (knobName in self._presetDictionary) and (self._presetDictionary[knobName] is not None):
      knob.setValue(self._presetDictionary[knobName])
    else:
      self.updatePresetValue(knob)

    return self.createProperty(knob.label(), knobName, values, knob.tooltip(), knob.visible(), knob.enabled())

  def enumKnobValues(self, enumKnob):
    """ Returns a list of all the valid key/value pairs for enumKnob. The
    passed in enumKnob is assumed to be an Enumeration_Knob. """
    values = enumKnob.values()
    values = [self.enumStringKeyValuePair(val) for val in values if self.enumStringKeyValuePair(val)]
    return values

  def enumStringKeyValuePair(self, str):
    """ Returns the enumeration knob entry's key/value pair for the passed in
    string as delineated by he tab whitespace character. Also checks if the
    display string matches the do not display label (see
    Enumeration_Knob::MenuItem::kMenuItemDontDisplayLabel). In which case None
    will be returned. If there is no tab whitespace character in the string then
    the display string is returned as both the key and value. """
    if '\t' in str:
      keyStr = str.split('\t')[0]
      displayStr = str.split('\t')[1]
      kDontDisplayStr = '\a'
      if displayStr != kDontDisplayStr:
        return displayStr, keyStr
    elif str:
      return str, str

    return None

  def updateProperties(self):
    """ Iterates through the property widgets and updates their state
    to reflect the current value and visibility of their associated knobs."""
    for item in self._knobs:
      knob = self._node.knobs()[item[0]]
      property = item[1]
      # temporarily disconnect
      property.propertyChanged.disconnect()

      self.updatePresetValue(knob)

      # The available options may have changed so update the property's
      # available values to update the items in the QComboBox
      if isinstance(knob, nuke.Enumeration_Knob):
        values = self.enumKnobValues(knob)
        property.setAvailableValues(values)

      # update property to reflect this
      property.update()
      # update visibility and enabled state
      property.parentWidget().layout().setWidgetVisible(property, knob.visible())
      property.setEnabled(knob.enabled())
      self.connectProperty(property)

  def updatePresetValue(self, knob):
    """ Sets the knob value in the preset dictionary if the knob is visible. If
    the knob isn't visible then the value is cleared as we don't want to store
    values of hidden knobs in the preset dictionary. This is so that we don't
    set the values on these hidden knobs on the node since setting the value
    of hidden knobs can have unintended consequences."""
    if knob.visible():
      isInt = knob.getFlag(self.STORE_INTEGER) and not isinstance(knob, nuke.Enumeration_Knob)
      self._presetDictionary[knob.name()] = int(knob.value()) if isInt else knob.value()
    else:
      self._presetDictionary[knob.name()] = None

  def propertyUpdated(self):
    """ Callback triggered when a UIProperty widget value has changed,
    this will update the value on the corresponding Write node knob and
    then call updateProperties to update the state of the other knobs."""
    property = self.sender()
    knob = self._node.knobs()[property._key]
    knob.setValue(self._presetDictionary[property._key])

    self.updateProperties()

  def connectProperty(self, propertyWidget):
    """ Connects the UIProperty to the propertyUpdated callback."""
    propertyWidget.propertyChanged.connect(self.propertyUpdated)

  def createDisclosureWidget(self, tabKnob, parentLayout):
    """ Creates a DisclosureButton and an associated widget that's visibility
    is toggled by the DisclosureButton. The widget and button are added to the
    passed in parentLayout. The widget itself has a TaskUIFormLayout set on it.
    Returns the created widget."""
    disclosureWidget = QtWidgets.QWidget()
    disclosureWidget.setLayout(TaskUIFormLayout())
    disclosureButton = DisclosureButton(False)
    disclosureButton.setText(tabKnob.label())
    parentLayout.addRow(disclosureButton)
    parentLayout.addRow(disclosureWidget)
    disclosureButton.addWidget(disclosureWidget)
    return disclosureWidget

  def knobOnNewLine(self, knob):
    """ Determines if a knob starts on a new row or is placed next
    to the previous knob."""
    return knob.getFlag(nuke.STARTLINE)

  def addWidgetsToNewRow(self, layout, labels, widgets):
    """ Adds widgets to the layout as a new row, adding them as
    multi widget rows as necessary, otherwise adding as a normal row
    if a single widget is provided (this is due to layout.setWidgetVisible
    behaving differently for multi widget rows which we don't want for
    a single widget row)."""
    if widgets:
      layout.addMultiWidgetRow(labels, widgets)

      del labels[:]
      del widgets[:]

  def initializeUI(self, propertyDictionaries):
    """ Iterates through the propertyDictionaries and creates UIProperties
    for each key in the dictionaries, where each key should be the name of a
    desired knob on the Write node. The UIProperties will store their values
    in the _presetDictionary, using the knob name as the key. If the
    _presetDictionary already has a value for the knob name, it will also
    initialise the UIProperty with that value."""
    labels = []
    widgets = []
    knobNames = []

    # Used to provide DisclosureButton functionality for closed Tab_Knob groups
    layoutStack = [ self._layout ]

    for properties in propertyDictionaries:
      knobNames.extend(properties.keys())

    # We use a range based for loop rather than a for-each loop
    # here as we want to iterate through the knobs in the order
    # they appear and calling knobs() on the node does not return
    # them in order.
    for n in range(0, self._node.numKnobs()):
      knob = self._node.knob(n)

      if isinstance(knob, nuke.Obsolete_Knob):
        continue

      knobName = knob.name()

      if isinstance(knob, nuke.Tab_Knob):
        # Tab_Knob.value() effectively returns true if the tab is open. In the
        # node a collapsible/expandable tab knob will report as closed since
        # they are created using BeginClosedGroup. The group is ended by using
        # EndGroup which will insert a Tab_Knob that is open. The code will
        # create a DisclosureWidget when it first encounters a closed Tab_Knob
        # and will add all subsequent knobs to that DisclosureWidget until it
        # reaches an open Tab_Knob. This approach almost certainly doesn't capture
        # the nuances of the different Tab_Knob::Types but works for our current
        # limited use case.
        isOpen = knob.value()
        if isOpen and (len(layoutStack) > 1):
          self.addWidgetsToNewRow(layoutStack[-1], labels, widgets)
          layoutStack.pop()
        elif not isOpen:
          self.addWidgetsToNewRow(layoutStack[-1], labels, widgets)
          # TODO don't add the DisclosureWidget if it has no child widgets
          disclosureWidget = self.createDisclosureWidget(knob, layoutStack[-1])
          layoutStack.append(disclosureWidget.layout())

      if self.knobOnNewLine(knob):
        self.addWidgetsToNewRow(layoutStack[-1], labels, widgets)

      if knobName in knobNames:
        knobNames.remove(knobName)
        uiProperty = self.createPropertyFromKnob(knob)
        label = uiProperty._label # we should use the label that the knob uses
        widgets.append(uiProperty)
        labels.append(label)

    # Add any remaining widgets
    self.addWidgetsToNewRow(layoutStack[-1], labels, widgets)

    assert len(knobNames) == 0, ("If this is false then not all of the knob names could be matched to knobs"
                                " on the Write node, suggesting the propertyDictionaries should be updated."
                                " Unmatched knobNames:\n" + ", ".join(str(name) for name in knobNames))
