# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

from PySide2 import (QtCore, QtGui, QtWidgets)

import hiero.core
import hiero.ui

import re


class TagFilterWidget (QtWidgets.QTableView):
  
  kCheckbox = 0
  kIcon     = 1
  kName     = 2
  
  tagSelectionChanged = QtCore.Signal(list, list)
  
  def __init__ (self, alltags, include_subset, exclude_subset, showhidden = False, parent = None):
    QtWidgets.QTableView.__init__(self, parent)
    self._alltags = [tag for tag in alltags if tag.visible() or showhidden]
    self._include_subset = include_subset
    self._exclude_subset = exclude_subset
    
    self.init_ui()
    
  def _tagSelectionChanged (self):
    self.tagSelectionChanged.emit(self.include_subset(), self.exclude_subset())
  
  def all_tags (self):
    """Return entire set of tags"""
    return self._alltags
  
  def include_subset (self):
    """Return subset for tags marked to be included"""
    return self._include_subset
  
  def exclude_subset (self):
    """Return subset of tags marked to be exclusion"""
    return self._exclude_subset
  
  class _TagCheckBox(QtWidgets.QCheckBox):
    tagCheckChanged = QtCore.Signal(tuple)
    
    def __init__(self, tag):
      QtWidgets.QCheckBox.__init__(self)
      self._tag = tag
      
      
      self.setTristate(True)
      self.setStyleSheet("::indicator {width:12px; height:12px;} ::indicator:indeterminate {image: url(icons:Checkbox_plus.png);} ::indicator:checked { image: url(icons:Checkbox_minus.png); }")
      
      self.stateChanged.connect(self._tagCheckChanged)
    
    def _tagCheckChanged(self, state):
      self.tagCheckChanged.emit((self._tag, state))
      pass
  
  class _TagFilterModel(QtCore.QAbstractTableModel):
    def __init__(self, view):
      QtCore.QAbstractTableModel.__init__(self)
      self._view = view
      self._checkboxes = {}
      pass
    
    def rowCount (self, parent):
      return len(self._view.all_tags())
    
    def columnCount (self, parent):
      return 3
    
    def _checkboxChanged ( self, param ):
      tag, state = param
      if state == QtCore.Qt.PartiallyChecked:
        if tag in self._view.exclude_subset():
          self._view.exclude_subset().remove(tag)
        self._view.include_subset().append(tag)
      
      elif state == QtCore.Qt.Checked:
        if tag in self._view.include_subset():
          self._view.include_subset().remove(tag)
        self._view.exclude_subset().append(tag)
      
      elif state == QtCore.Qt.Unchecked:
        if tag in self._view.include_subset():
          self._view.include_subset().remove(tag)
        if tag in self._view.exclude_subset():
          self._view.exclude_subset().remove(tag)
      
      self._view._tagSelectionChanged()
    
    def data ( self, index, role ):
      
      if role == QtCore.Qt.DisplayRole:
        if index.column() == TagFilterWidget.kCheckbox:
          indexkey = str((index.row(), index.column()))
          if indexkey not in self._checkboxes:
            
            tag = self._view.all_tags()[index.row()]
            
            checkbox = TagFilterWidget._TagCheckBox(tag)
            
            if tag in self._view.include_subset():
              checkbox.setCheckState(QtCore.Qt.PartiallyChecked)
            elif tag in self._view.exclude_subset():
              checkbox.setCheckState(QtCore.Qt.Checked)
            else:
              checkbox.setCheckState(QtCore.Qt.Unchecked)
            checkbox.tagCheckChanged.connect(self._checkboxChanged)
            self._checkboxes[indexkey] = checkbox

            # Create a container widget and set margins on it, this is the simplest way of shifting
            # the checkbox a few pixels to the right.
            checkBoxContainer = QtWidgets.QWidget()
            checkBoxContainerLayout = QtWidgets.QHBoxLayout()
            checkBoxContainerLayout.setContentsMargins(5, 0, 0, 0)
            checkBoxContainer.setLayout(checkBoxContainerLayout)
            checkBoxContainerLayout.addWidget(checkbox)

            self._view.setIndexWidget(index, checkBoxContainer)
          
          pass
        elif index.column() == TagFilterWidget.kName:
          tag = self._view.all_tags()[index.row()]
          return tag.name()
      
      elif role == QtCore.Qt.DecorationRole:
        if index.column() == TagFilterWidget.kIcon:
          tag = self._view.all_tags()[index.row()]
          return QtGui.QIcon(tag.icon())
      
      else:
        pass
      
      pass
  

  def init_ui(self):
    self.setLayout(QtWidgets.QVBoxLayout())
    self.setModel(self._TagFilterModel(self))
    self.verticalHeader().setVisible(False)
    self.horizontalHeader().setVisible(False)
    self.setShowGrid(False)
    
    # Resize cells
    self.setColumnWidth(TagFilterWidget.kCheckbox, 20)
    self.setColumnWidth(TagFilterWidget.kIcon, 20)
    self.horizontalHeader().setStretchLastSection(True)
    self.resizeRowsToContents()



#w = TagFilterWidget([hiero.core.Tag("TagA"), hiero.core.Tag("TagB"), hiero.core.Tag("TagC")], [], [])
#w.show()



