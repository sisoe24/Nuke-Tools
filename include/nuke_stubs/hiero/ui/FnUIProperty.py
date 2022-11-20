import re
import sys
import hiero.core
import os.path
from PySide2 import (QtCore, QtGui, QtWidgets)

import hiero.ui

from hiero.core.FnFloatRange import FloatRange, IntRange, Default, QuicktimeSettings, QuicktimeCodec, CustomList
import types

class UIPropertyFactory(object):
  """Factory for registering and creating UIProperties"""
  
  # Static dictionary
  PropertyDictionary = {}
  @staticmethod
  def register (valuetypes, objecttype):
  
    if hasattr(valuetypes, "__iter__"):
      for valuetype in valuetypes:
        UIPropertyFactory.PropertyDictionary[valuetype] = objecttype
    else:
      UIPropertyFactory.PropertyDictionary[valuetypes] = objecttype
    
    pass
    
  @staticmethod
  def unregister (valuetype, objecttype):
    del UIPropertyFactory.PropertyDictionary[objecttype]
    pass
    
  @staticmethod
  def create ( type, **kargs ):
    if type in UIPropertyFactory.PropertyDictionary:
      objecttype = UIPropertyFactory.PropertyDictionary[type]
      return objecttype (**kargs)
    return None

class UIPropertyBase(QtWidgets.QWidget):
  """UIProperty is a utility class which reflects data into a suitable Widget"""
  
  # Signal fired whenever properties are updated
  propertyChanged = QtCore.Signal()
   
  def __init__ (self, key=None, value=None, dictionary=None, label=None, tooltip=None, addWidgetHandler=None):
    """@param key - Key against which to store value
       @param value - Value, type of which will determine UI widget
       @param dictionary - dictionary in which value will be saved (against key)
       @param label - Text Label to identify property. (optional, will default to key) 
       @param tooltip - Tooltip describing property"""
    QtWidgets.QWidget.__init__(self)
    
    if label == None:
      label = key
    self._label = label
    self._key = key
    self._value = value  
    self._dictionary = dictionary
    self._tooltip = tooltip
    self._addWidgetHandler = addWidgetHandler
   
    assert self._key is not None
    assert self._value is not None
    assert self._dictionary is not None


  def update(self, commit=False):
    """ Update the property.  If commit is True, the current UI value is written back to the
        properties dict.  This seems to be mostly useful when the value may not yet exist in
        the dict and should be set to a default. """
    raise NotImplementedError()

  def setAvailableValues(self, value):
    """ Update the available values. This is relevant for properties where the value passed in on
        creation is used to create the available options, e.g. a ComboBox, rather than simply
        being used to determine the type of property to create. This is useful when the available
        options can change e.g. ComboBox options that change depending on another property.
        The values provided are assumed to be the same type as those used to create the property. """
    raise NotImplementedError()

  @staticmethod
  def register (valuetypes, objecttype):
    UIPropertyFactory.register(valuetypes, objecttype)


def getLabelData(item):
  if isinstance( item, tuple ):
    label, data = item
  else:
    label, data = str(item), str(item)
  return label, data


class ComboProperty(UIPropertyBase):
  def __init__(self, stretch=0.7, **kargs):
    UIPropertyBase.__init__(self, **kargs)
    
    layout = QtWidgets.QHBoxLayout()
    self.setLayout(layout)
    layout.setContentsMargins(0, 0, 0, 0)
    
    # Combo box required value to be an itterable type
    assert hasattr(self._value, "__iter__")    
        
    self._widget = QtWidgets.QComboBox()
    self._widget.setToolTip(self._tooltip)
    layout.addWidget(self._widget,stretch) 

    index = 0  
    defaultIndex = None     
    presetValid = False

    self.populateComboBox()

    if self._addWidgetHandler != None:
      self._addWidgetHandler(self._widget, layout, None)
      
    self.update()

    self._widget.currentIndexChanged.connect(self.comboChanged)

  def populateComboBox(self):
    self._widget.clear()
    for listitem in self._value:
      label,data = getLabelData(listitem)
      self._widget.addItem(label, data)

  def update (self, commit=False):
    presetValue = self._dictionary[self._key] if self._key in self._dictionary else None 
      
    defaultIndex = None
    presetIndex = None
    for index, listitem  in enumerate(self._value):
      _, data = getLabelData(listitem)
      if presetValue is not None and str(data) == str(presetValue):
        presetIndex = index
      if isinstance(data, Default):
        defaultIndex = index

    if presetIndex is not None:
      self._widget.setCurrentIndex(presetIndex)
    elif defaultIndex is not None:
      self._widget.setCurrentIndex(defaultIndex)

    if commit:
      self._dictionary[self._key] = str(self._widget.itemData(self._widget.currentIndex()))

  def setAvailableValues(self, value):
    self._value = value
    # Block signals as rebuilding the QComboBox will cause the current item to
    # change which will overwrite our _dictionary value.
    self._widget.blockSignals(True)
    self.populateComboBox()
    # Call update to attempt to restore the previous selection from _dictionary
    # Pass True in so that _dictionary gets updated if the previous selection is
    # no longer available.
    self.update()
    self._widget.blockSignals(False)

  def comboChanged(self, index):
    self._dictionary[self._key] = str(self._widget.itemData(self._widget.currentIndex()))
    self.propertyChanged.emit()
    
  def setFloatValue(self, newValue, floatTolerance = 0.01):
    '''sets the combobox value to the newValue, assuming it can find a string item in the list that is within floatTolerance of the newValue'''
    i = 0
    while i < self._widget.count():
      itemValue = float(self._widget.itemText(i))
      difference = abs(itemValue - newValue)
      if difference <= floatTolerance:
        self._widget.setCurrentIndex(i)
        self._dictionary[self._key] = self._widget.currentText()
        break
      i += 1

UIPropertyBase.register((tuple, list), ComboProperty)



class CascadingEnumerationComboBox(QtWidgets.QComboBox):
  """ Combo box specialisation for supporting the cascading enumeration
  property.
  """

  kSeparator = '/'

  def __init__(self, values):
    QtWidgets.QComboBox.__init__(self)

    # Build the menu structure
    rootMenu = QtWidgets.QMenu()
    rootMenu.triggered.connect(self.onActionTriggered)
    self._rootMenu = rootMenu
    subMenuMap = dict()
    self._actions = []

    # Function to recursively build sub-menus for placing actions in
    def getActionMenu(components):
      if not components: # list is empty, return the root
        return rootMenu
      else:
        # If this menu already exists, return it, otherwise to a recursive call
        # to get the parent, and create it
        key = CascadingEnumerationComboBox.kSeparator.join(components)
        if key in subMenuMap:
          return subMenuMap[key]
        else:
          parentMenu = getActionMenu(components[:-1])
          menu = parentMenu.addMenu(components[-1])
          subMenuMap[key] = menu
          return menu

    # Each value is possibly in / separated path form.  The last part is the
    # name, the earlier parts are used for constructing menus.
    for value in values:
      components = value.split(CascadingEnumerationComboBox.kSeparator)
      actionName = components[-1]
      actionMenu = getActionMenu(components[:-1])
      action = actionMenu.addAction(actionName)
      action.setCheckable(True)
      self.addItem(actionName)
      self._actions.append(action)


  def showPopup(self):
    """ Override default showPopup() and show our menu instead """
    QtWidgets.QComboBox.hidePopup(self)
    self._rootMenu.popup( self.mapToGlobal(QtCore.QPoint(0, self.height())) )


  def setCurrentIndex(self, index):
    """ Set the current index and set the checked state of the menu entries. """
    QtWidgets.QComboBox.setCurrentIndex(self, index)
    text = self.itemText(index)
    for action in self._actions:
      action.setChecked( action.text() == text )


  def onActionTriggered(self, action):
    """ Callback from a menu action being triggered, set the index. """
    index = self._actions.index(action)
    self.setCurrentIndex(index)



class CascadingEnumerationProperty(UIPropertyBase):
  """ Property widget which cascades items into sub-menus when the text has /
  separators, in a similar way to the Nuke cascading enumeration knob.
  """
  def __init__(self, stretch=0.7, **kargs):
    UIPropertyBase.__init__(self, **kargs)

    layout = QtWidgets.QHBoxLayout()
    self.setLayout(layout)
    layout.setContentsMargins(0, 0, 0, 0)

    # Combo box required value to be an itterable type
    assert hasattr(self._value, "__iter__")

    self._widget = CascadingEnumerationComboBox(self._value)
    self._widget.setToolTip(self._tooltip)
    layout.addWidget(self._widget,stretch)

    if self._addWidgetHandler != None:
      self._addWidgetHandler(self._widget, layout, None)

    self.update()

    self._widget.currentIndexChanged.connect(self.onComboChanged)


  def update (self, commit=False):
    propertyType = type(self._value)
    presetValue = self._dictionary[self._key] if self._key in self._dictionary else None

    defaultIndex = None
    presetIndex = None
    for index, listitem in enumerate(self._value):

      listitem = listitem.split(CascadingEnumerationComboBox.kSeparator)[-1]

      if presetValue is not None and str(listitem) == str(presetValue):
        presetIndex = index
      if isinstance(listitem, Default):
        defaultIndex = index

    if presetIndex is not None:
      self._widget.setCurrentIndex(presetIndex)
    elif defaultIndex is not None:
      self._widget.setCurrentIndex(defaultIndex)

    if commit:
      self._dictionary[self._key] = self._widget.currentText()


  def onComboChanged(self, index):
    """ Slot callback when the combo box current item changes. """
    self._dictionary[self._key] = self._widget.currentText()
    self.propertyChanged.emit()



class TextProperty(UIPropertyBase):
  
  def __init__(self, **kargs):
    UIPropertyBase.__init__(self, **kargs)
    
    layout = QtWidgets.QHBoxLayout()
    self.setLayout(layout)
    layout.setContentsMargins(0, 0, 0, 0)
        
    self._widget = QtWidgets.QLineEdit()
    self._widget.setToolTip(self._tooltip)
    layout.addWidget(self._widget)
  
    self.update()
      
    if self._addWidgetHandler != None:
      self._addWidgetHandler(self._widget, editLayout, None)
    self._widget.textChanged.connect(self.lineditChanged)
      
    propertyType = type(self._value)
    if propertyType is int:
      self._widget.setValidator(QtGui.QIntValidator(self._widget));
      self._widget.setSizePolicy( QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
    if propertyType is float:
      self._widget.setValidator(QtGui.QDoubleValidator(self._widget));
      self._widget.setSizePolicy( QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)


  def update (self, commit=False):
    
    propertyType = type(self._value)
    presetValue = self._dictionary[self._key] if self._key in self._dictionary else None

    if presetValue is not None:
      self._widget.setText(str(presetValue))   
    else:
      self._widget.setText(str(self._value)) 
      
    if commit:
      self._dictionary[self._key] = type(self._value)(self._widget.text())
            
  def lineditChanged ( self, value ):    
    self._dictionary[self._key] = type(self._value)(value)
    self.propertyChanged.emit()

UIPropertyBase.register((str, bytes, int, float), TextProperty)

class CheckboxProperty(UIPropertyBase):
  
  def __init__(self, **kargs):
    UIPropertyBase.__init__(self, **kargs)
    
    layout = QtWidgets.QHBoxLayout()
      
    self.setLayout(layout)
    layout.setContentsMargins(0, 0, 0, 0)
        
    self._widget = QtWidgets.QCheckBox()
    self._widget.setToolTip(self._tooltip)
    
    layout.addWidget(self._widget)

    self.update()
    
    self._widget.stateChanged.connect(self.checkboxChanged)        

    if self._addWidgetHandler != None:
      self._addWidgetHandler(self._widget, layout, None)

  def update (self, commit=False):
    
    propertyType = type(self._value)
    presetValue = self._dictionary[self._key] if self._key in self._dictionary else None

    checked = presetValue
    if presetValue is None:
      checked = self._value
      
    if checked:
      self._widget.setCheckState(QtCore.Qt.Checked)
    else:
      self._widget.setCheckState(QtCore.Qt.Unchecked)
      
    if commit:
      self._dictionary[self._key] = checked
    
  def checkboxChanged (self, state):
    self._dictionary[self._key] = state == QtCore.Qt.Checked
    self.propertyChanged.emit()

UIPropertyBase.register(bool, CheckboxProperty)


class SliderProperty(UIPropertyBase):
  """ Class which shows a UI for numeric ranges. """

  __floatSliderMin = 0
  __floatSliderMax = 1000
  
  def __init__(self, **kargs):
    UIPropertyBase.__init__(self, **kargs)

    self._handlingUserEdit = False
    
    layout = QtWidgets.QHBoxLayout()
      
    self.setLayout(layout)
    layout.setContentsMargins(0, 0, 0, 0)
        
    layout.addWidget(QtWidgets.QLabel(str(self._value.min())))
    self._slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    self._lineEdit = QtWidgets.QLineEdit()
    
    self._slider.setToolTip(self._tooltip)
    self._lineEdit.setToolTip(self._tooltip)
    
    self.update()

    # If showing an int range, adjust the line edit width according to the range, otherwise it's fixed.
    # Also add appropriate validators
    if self.isIntRange():
      textMaxWidth = 30
      if self._value.range() > 100000:
        textMaxWidth = 60
      if self._value.range() > 1000000:
        textMaxWidth = 80
      self._lineEdit.setValidator(QtGui.QIntValidator(self._lineEdit))
    else:
      textMaxWidth = 60
      self._lineEdit.setValidator(QtGui.QDoubleValidator(self._lineEdit))

    self._lineEdit.setMaximumWidth(textMaxWidth)
   
    # Set the range of the slider, for an int range this is just the values we have, for floats
    # use a fixed range which is mapped to the float value.
    if self.isIntRange():
      self._slider.setRange(self._value.min(), self._value.max())
    else:
      self._slider.setRange(SliderProperty.__floatSliderMin, SliderProperty.__floatSliderMax)

    layout.addWidget(self._slider)
    layout.addWidget(QtWidgets.QLabel(str(self._value.max())))
    layout.addWidget(self._lineEdit)
    
    self._slider.sliderReleased.connect(self.onSliderReleased)
    self._slider.valueChanged.connect(self.onSliderValueChanged)
    self._lineEdit.textEdited.connect(self.onLineEditTextEdited)

    if self._addWidgetHandler != None:
      self._addWidgetHandler(self._slider, editLayout, None)


  def isIntRange(self):
    """ Check if the slider is representing an int range. """
    return isinstance(self._value, IntRange)


  def valueFromLineEdit(self):
    """ Get the value from the line edit widget, as either an int or float depending on
        the range type. """
    text = self._lineEdit.text()
    if self.isIntRange():
      return int(text)
    else:
      return float(text)


  def valueFromSlider(self):
    """ Get the value from the line edit widget, as either an int or float depending on the range type. """
    value = self._slider.value()
    # If representing a float range, map the slider value
    if not self.isIntRange():
      value = self._value.min() + ((float(value) / float(SliderProperty.__floatSliderMax)) * self._value.range())
    return value


  def setSliderValue(self, value):
    """ Set the slider value. """
    # Block the slider's signals so onSliderValueChanged doesn't get called from here
    self._slider.blockSignals(True)
    if self.isIntRange():
      self._slider.setValue(value)
    else:
      value -= self._value.min()
      self._slider.setValue(int((float(SliderProperty.__floatSliderMax) / float(self._value.range())) * value))
    self._slider.blockSignals(False)


  def update(self, commit=False):
    if self._handlingUserEdit:
      return

    # Initialise to default value
    value = self._value.default()

    # Try to look up value in dictionary
    if self._key in self._dictionary:
      if self._dictionary[self._key] is not None:
        value = self._dictionary[self._key]

    # Update UI
    self.setSliderValue(value)
    self._lineEdit.setText(str(value))
    
    # Commit value back to the dictionary
    if commit:
      self._dictionary[self._key] = self.valueFromLineEdit()


  def onLineEditTextEdited( self, text ):
    """ Callback when line edit text is edited. """
    # Prevent callbacks from changing the text while the user is typing
    self._handlingUserEdit = True
    value = self.valueFromLineEdit()
    self.setSliderValue(value)
    self._dictionary[self._key] = value
    self.propertyChanged.emit()
    self._handlingUserEdit = False
    

  def onSliderReleased( self ):
    """ Callback when slider is released, send property changed notifications. """
    value = self._slider.value()
    self.onSliderValueChanged(value)
    self.propertyChanged.emit()
    

  def onSliderValueChanged( self, value ):
    """ Callback when slider value changes. """
    self._lineEdit.setText(str(self.valueFromSlider()))
    self._dictionary[self._key] = self.valueFromLineEdit()

    # Don't send this while the slider is being dragged, it will be done on release.
    if not self._slider.isSliderDown():
      self.propertyChanged.emit()


UIPropertyBase.register((hiero.core.FnFloatRange.FloatRange, hiero.core.FnFloatRange.IntRange), SliderProperty)

class CustomComboProperty(ComboProperty):
  def __init__(self, **kargs):  
    self._default = kargs["value"].default()
    kargs["value"] = list(kargs["value"].values())    
    ComboProperty.__init__(self, stretch=1.0, **kargs)
    
    self._widget.setToolTip(self._tooltip)
    self._widget.setEditable(True)
    self._lineEdit = self._widget.lineEdit()
    
    self.update()
          
    self._lineEdit.editingFinished.connect(self.customTextChanged)
    
  def update (self, commit=False):
    propertyType = type(self._value)
    presetValue = self._dictionary[self._key] if self._key in self._dictionary else None 

    defaultValue, value = None, None
    defaultIndex = None
    presetIndex = None
    for listitem, index in zip(self._value, list(range(0, len(self._value)))):
        
      if presetValue is not None and str(listitem) == str(presetValue):
        presetIndex = index
        value = listitem
      if isinstance(listitem, Default) or str(self._default) == str(listitem):
        defaultIndex = index
        defaultValue = listitem

    if presetIndex is not None:
      self._widget.setCurrentIndex(presetIndex)
    elif presetValue is not None:      
      self._widget.setEditText(presetValue)
      value = presetValue
    elif defaultIndex is not None:
      self._widget.setCurrentIndex(defaultIndex)
      value = defaultValue


    if commit:
      self._dictionary[self._key] = value
  
  def checkValidation(self):    
    if self._lineEdit.validator():
      text = self._lineEdit.text()
      state = self._lineEdit.validator().validate(text, 0)
      if state != QtGui.QValidator.Acceptable:
        return False
    return True

    
  def customTextChanged(self):
    value = self._lineEdit.text()
    self._dictionary[self._key] = value
    self.propertyChanged.emit()
    
UIPropertyBase.register(hiero.core.FnFloatRange.CustomList, CustomComboProperty)


class ViewsPropertyWidget(UIPropertyBase):
  """ Widget for selecting views. The UI follows the Write node 'views' knob """
  def __init__(self, **kwargs):
    UIPropertyBase.__init__(self, **kwargs)
    layout = QtWidgets.QHBoxLayout()
    self.setLayout(layout)
    layout.setContentsMargins(0, 0, 0, 0)

    self._actions = []
    self._menu = QtWidgets.QMenu()
    for view in self.views():
      action = self._menu.addAction(view)
      self._actions.append(action)
      action.setCheckable(True)
      action.toggled.connect(self.onViewToggled)

    self._button = QtWidgets.QToolButton()
    self._button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
    self._button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
    self._button.setMenu(self._menu)
    layout.addWidget(self._button)
    self.update(False)

  def views(self):
    """ List of available views """
    return self._value

  def update(self, commit=False):
    if commit:
      # Store the selected views. If all are selected store 'all' rather than the individual views
      selectedViews = [v for v, a in zip(self.views(), self._actions) if a.isChecked()]
      if len(selectedViews) == len(self.views()):
        selectedViews = hiero.core.RenderTaskPreset.AllViews()
      self._dictionary[self._key] = selectedViews
    else:
      # Update the UI to match the stored selection
      selectedViews = self._dictionary[self._key]
      isViewSelected = lambda view: (selectedViews == hiero.core.RenderTaskPreset.AllViews()) or view in selectedViews
      for view, action in zip(self.views(), self._actions):
        action.setChecked(isViewSelected(view))

    # Update button label
    if not selectedViews:
      text = '[none]'
    elif selectedViews == hiero.core.RenderTaskPreset.AllViews():
      text = ', '.join(self.views())
    else:
      text = ', '.join(selectedViews)
    self._button.setText(text)

  def onViewToggled(self, checked):
    self.update(True)
    self.propertyChanged.emit()
