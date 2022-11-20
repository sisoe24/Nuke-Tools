# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

from PySide2 import (QtCore, QtGui, QtWidgets)

import hiero.core

import re

from .FnExternalRender import kPerShot, kPerTrack, kPerSequence, kUnconnected, kDisabled
from . import FnAdditionalNodesDialog


class ScriptEdit(QtWidgets.QTextEdit):
  """QText edit with syntax highlighting and automatic removal of various expression when pasting a nuke script"""
  
  # These are the expressions to be removed from pasted nuke scripts
  expressionsForRemoval = [ QtCore.QRegExp("^set cut_paste_input \[stack \d\]\s*"),
                            QtCore.QRegExp("push \$cut_paste_input\s*"),
                            QtCore.QRegExp("^version[^\n\r]+\s*"),
                            QtCore.QRegExp("\s+[x|y]pos [-\d]+")]
  
  class Highlighter (QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None):
      QtGui.QSyntaxHighlighter.__init__(self, parent)
      
      self._rules = []
      nodeNameFormat = QtGui.QTextCharFormat()
      nodeNameFormat.setForeground(QtCore.Qt.magenta)
      nodeNameFormat.setFontWeight(QtGui.QFont.Bold)
      self._rules.append( (QtCore.QRegExp("(\w+)\s*\{"),  nodeNameFormat) )
      
      braceFormat = QtGui.QTextCharFormat()
      braceFormat.setForeground(QtCore.Qt.yellow)
      braceFormat.setFontWeight(QtGui.QFont.Bold)
      self._rules.append( (QtCore.QRegExp("(\{|\})"),  braceFormat) )
      
      literalFormat = QtGui.QTextCharFormat()
      literalFormat.setForeground(QtCore.Qt.red)
      self._rules.append( (QtCore.QRegExp("(\".+\")"),  literalFormat) )
    
    def highlightBlock(self, text):
      
      # Walk list of rules
      for rule in self._rules:
        regex, format = rule
        # Look for regex matchs
        index = regex.indexIn(text, 0)
        while (index >= 0):
          index = text.find(regex.cap(1), index, len(text))
          length = len(regex.cap(1))
          self.setFormat(index, length, format)
          index = regex.indexIn(text, index + length)
  
  def __init__ (self):
    QtWidgets.QTextEdit.__init__(self)
    self._highlighter = self.Highlighter(self.document())
  
  def insertFromMimeData (self, source):
    # Duplicate the mimedata so that it can be modified and passed on
    newSource = QtCore.QMimeData(source)
    # Mime data from nuke will be in text form
    if source.hasText():
      text = source.text()
      
      # Look for matches of each of the removal expresions
      for regex in self.expressionsForRemoval:
        index = regex.indexIn(text, 0)
        while (index >= 0):
          # Loop until all instances are removed
          text = text.replace(regex.cap(0), "")
          index = regex.indexIn(text, index)
        
        # update mime data with stripped text
        newSource.setText(text)
    
    # Pass modified mime data to base class to handle paste
    return QtWidgets.QTextEdit.insertFromMimeData(self, newSource)



class AdditionalNodesDialog (QtWidgets.QDialog):
  """Dialog containing a list of instuctions for inserting additional nuke nodes into generated nuke scripts"""
  
  class ItemModel (QtCore.QAbstractItemModel):
    """ Item model for the AdditionalNodesDialog. This is a table structure, so 
    while the internal Element class was implemented with support for trees of 
    elements this is not used apart from the fact that there is a _root element 
    which has a list of children that are exposed in the model.
    """

    class Element(QtCore.QObject):
      """Each element represents one insertion instruction, composite pattern to aid implimentation of the AbstractItemModel.
        In hindsight, could have probably used a StandardListView.
        Element is responsible for creating and managing the widgets which are added to the QAbstractItemView"""
      
      # Signal fired whenever properties are updated
      propertyChanged = QtCore.Signal()
      
      #  Signal fired when remove button is clicked
      removeClicked = QtCore.Signal(QtCore.QObject)
      
      def __init__(self, parent, location = None, tags = [], script = None, available_tags = []):
        QtCore.QObject.__init__(self)
        self._location = location
        self._tags = list(tags)
        self._available_tags = available_tags
        self._script = script
        self._parent = parent
        
        # Composite pattern to aid implimentation of the AbstractItemModel
        # In reality not nested, only root node contains children.
        self._children = []
        
        self._locationWidget = None
        self._tagsWidget = None
        self._scriptWidget = None
        
        # Create a combo box for Location instruction
        self._locationWidget = QtWidgets.QComboBox()
        locations = [kPerShot, kPerTrack, kPerSequence, kUnconnected, kDisabled]
        for index, loc in zip(list(range(0, len(locations))), locations):
          self._locationWidget.addItem(loc)
          if loc == location:
            self._locationWidget.setCurrentIndex(index)
        self._locationWidget.currentIndexChanged.connect(self._locationChanged)
        #self._locationWidget.setFrame(False)
        
        
        # Create a list view with checkboxes for the list of available tags
        self._tagsWidget = QtWidgets.QListView()
        tagsModel = QtGui.QStandardItemModel()
        self._tagsWidget.setModel(tagsModel)
        self._locationChanged(self._locationWidget.currentIndex())
        tagsModel.itemChanged.connect(self._tagsChanged)
        self._tagsWidget.setAutoFillBackground(True)
        
        # Create instance of custom ScriptEdit widget (has highlighting and custom paste behaviour)
        self._scriptWidget = ScriptEdit()
        self._scriptWidget.setText(script)
        self._scriptWidget.textChanged.connect(self._scriptChanged)
        self._scriptWidget.setAutoFillBackground(True)
        
        # create remove button and connect to function which fires the removeClicked signal
        # This should be connected and handled by the parent QAbstracItemModel
        self._removeWidget = QtWidgets.QPushButton(QtGui.QIcon("icons:ExportCancel.png"), "")
        self._removeWidget.clicked.connect(self._remove)
        self._removeWidget.setFlat(True)
      
      def _remove(self):
        # Fire removeClicked signal to be handled by parent QAbstractItemModel
        self.removeClicked.emit(self)
      
      def _locationChanged(self, index):
        # Update the property from the combo widget
        self._location = self._locationWidget.itemText(index)

        tags = self._tags[:]
        tagsModel = self._tagsWidget.model()
        tagsModel.clear()
        
        typeMap = {kPerShot : (hiero.core.Clip, hiero.core.TrackItem, hiero.core.VideoTrack, hiero.core.AudioTrack, hiero.core.Sequence), 
                   kPerTrack : (hiero.core.VideoTrack, hiero.core.AudioTrack, hiero.core.Sequence), 
                   kPerSequence : (hiero.core.Sequence,), 
                   kUnconnected : (hiero.core.Clip, hiero.core.TrackItem, hiero.core.VideoTrack, hiero.core.AudioTrack, hiero.core.Sequence), 
                   kDisabled : []}
                   
        tagsAdded = []

        for tag, parentType in self._available_tags:
          # Dont add tags with duplicate names
          if tag.name() not in tagsAdded and parentType in typeMap[self._location]:
            item = QtGui.QStandardItem(QtGui.QIcon(tag.icon()), tag.name())
            tagsAdded.append(tag.name())
            tagsModel.appendRow(item)
            item.setCheckable(True)
            if tag.name() in tags:
              item.setCheckState(QtCore.Qt.Checked)

      
      def _tagsChanged(self, item):
        # Update list of tags based on the checkbox state of the item which has changed
        tagName = item.text()
        if item.checkState() == QtCore.Qt.Checked:
          if tagName not in self._tags:
            self._tags.append(tagName)
        else:
          if tagName in self._tags:
            self._tags.remove(tagName)
      
      def _scriptChanged(self):
        # Update the script property from the ScriptEdit widget
        self._script = self._scriptWidget.toPlainText()
      
      
      def data (self):
        # Return a tuple of the properties
        return self._location, self._tags, self._script
      
      def location (self):
        return self._location
      def locationWidget (self):
        return self._locationWidget
      
      def tags (self):
        return self._tags
      def tagsWidget (self):
        return self._tagsWidget
      
      def script (self):
        return self._script
      def scriptWidget (self):
        return self._scriptWidget
      
      def child (self, index):
        return self._children[index]
      def parent (self):
        return self._parent
      def childIndex (self, child):
        if child in self._children:
          return self._children.index(child)
        return 0
      
      def addChild (self, child):
        self._children.append(child)
      
      def removeChild (self, child):
        if child in self._children:
          self._children.remove(child)
      
      def childCount (self):
        return len(self._children)
      
      def removeWidget (self):
        return self._removeWidget
    
    def __init__(self, view, data, available_tags):
      QtCore.QAbstractItemModel.__init__(self)
      self._view = view
      self._data = data
      self._tags = available_tags
      self._root = self.Element(None)

      self.beginResetModel()
      
      for location, tags, script in self._data:
        element = self.Element(self._root, location=location, tags=tags, script=script, available_tags=available_tags)
        element.removeClicked.connect(self.removeItem)
        self._root.addChild(element)

      self.endResetModel()
    
    def addItem (self, location = None, tags = [], script = None):
      self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
      
      element = self.Element(self._root, available_tags=self._tags)

      element.removeClicked.connect(self.removeItem)
      self._root.addChild(element)
      
      self.endInsertRows()
    
    def removeItem (self, element):
      row = self._root.childIndex(element)
      
      self.beginRemoveRows(QtCore.QModelIndex(), row, row)
      
      self._root.removeChild(element)
      
      self.endRemoveRows()
      
              
    def clear(self):
      # Clear all entries
      self.beginRemoveRows(QtCore.QModelIndex(), 0, self.rowCount())

      self._root._children = []
      
      self.endRemoveRows()

    def data(self, index, role):
      if not index.isValid():
        return None
      
      if role == QtCore.Qt.ToolTipRole:
        return self._tooltip(index)
        
      if role != QtCore.Qt.DisplayRole:
        return None
      
      element = self.elementForIndex(index)
      data = None
      column = index.column()
      
      if column == 1:
        widget = element.locationWidget()
      elif column == 2:
        
        widget = element.tagsWidget()
      elif column == 3:
        
        widget = element.scriptWidget()
      elif column == 0:
        widget = element.removeWidget()
      
      
      # Rather than return the data as a string, here we check the content of the indexWidget
      # If this is not the custom widget created within the Element, set widget as the content of that cell
      currentWidget = self._view.indexWidget(index)
      if widget != currentWidget:
        widget.setToolTip(self._tooltip(index))
        self._view.setIndexWidget(index, widget)

      return data
    
    def _tooltip (self, section):
      if section == 1:
        return "Location within the script to insert additional nodes."
      elif section == 2:
        return "Tags which trigger the insertion of additional nodes. No tags means every item will have additional nodes applied"
      elif section == 3:
        return "Nuke script in text form, can be copied and pasted from Nuke. If more than one node, consider using a Group."

    def headerData (self, section, orientation, role = QtCore.Qt.DisplayRole ):
      if orientation == QtCore.Qt.Horizontal:
        if role == QtCore.Qt.DisplayRole:
          if section == 1:
            return "Apply To"
          elif section == 2:
            return "Tags"
          elif section == 3:
            return "Script"
        
        if role == QtCore.Qt.ToolTipRole:
          return self._tooltip(section)
          
      return None
    
    def flags(self, index):
      if not index.isValid():
        return 0
      
      return QtCore.Qt.ItemIsEnabled

    def elementForIndex(self, index):
      """ Get the Element object for a given index. This will be a child of the 
      root element. 
      """
      if index.isValid():
        return self._root.child(index.row())
      else:
        return None
    
    def index(self, row, column, parent = QtCore.QModelIndex()):
      if  not self.hasIndex(row, column, parent):
        return QtCore.QModelIndex()
      else:
        return self.createIndex(row, column)
    
    def parent(self, index):
      return QtCore.QModelIndex()
    
    def rowCount(self, parent = QtCore.QModelIndex()):
      if parent.isValid():
        return 0
      else:
        return self._root.childCount()
    
    def columnCount(self, parent = QtCore.QModelIndex()):
      return 4
  
  def __init__ (self, data, tags):
    QtWidgets.QDialog.__init__(self)
    self._itemView = QtWidgets.QTableView()
    self._model = self.ItemModel(self._itemView, data, tags)
    self._itemView.setModel(self._model)
    
    self.setWindowTitle("Additional Nodes Setup")
    self.init_ui()
  
  def init_ui(self):
    self.setLayout(QtWidgets.QVBoxLayout())
    self._itemView.verticalHeader().setDefaultSectionSize(100)
    self._itemView.verticalHeader().hide()
    self._itemView.setColumnWidth(0, 30)
    self._itemView.setColumnWidth(1, 120)
    self._itemView.setColumnWidth(2, 200)
    self._itemView.horizontalHeader().setStretchLastSection(True)
    self.resize(750, 300)
    self.setModal(True)
    
    self.layout().addWidget(self._itemView)
    
    self._standardButtons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
    addButton = self._standardButtons.addButton("+", QtWidgets.QDialogButtonBox.ActionRole)
    addButton.clicked.connect(self._addEntry)
    
    clearButton = self._standardButtons.addButton("Clear", QtWidgets.QDialogButtonBox.ActionRole)
    clearButton.clicked.connect(self._clear)
    
    self._standardButtons.accepted.connect(self.accept)
    self._standardButtons.rejected.connect(self.reject)
    #self.layout().addStretch(1)
    self.layout().addWidget(self._standardButtons)
  
  def _addEntry(self):
    # These are the default values for new entires
    location, tags, script = kPerShot, [], ""
    self._model.addItem(location=location, tags=tags, script=script)
  
  def _clear(self):
    self._model.clear()
  
  def _removeEntry(self, widget):
    self.layout().removeWidget(widget)
    self._widgets.remove(widget)
    widget.hide()
    del widget
    
    pass
  
  def data(self):
    data = []
    for element in self._model._root._children:
      data.append(element.data())
    return data

  def cleanup(self):
    # CC: make sure we release the all elements before closing the panel;
    # TP #200161
    self._clear()
  
  def accept(self):
    QtWidgets.QDialog.accept(self)
    pass
  
  def reject(self):
    QtWidgets.QDialog.reject(self)
    pass

FnAdditionalNodesDialog.AdditionalNodesDialog = AdditionalNodesDialog

"""
  dummydata = ( ( kPerWrite, ("Green Screen",), "KeyLight {}"), (kPerWrite, ("Reference",), "Text{}"),)
  dummytags = (hiero.core.Tag("Green Screen"), hiero.core.Tag("Reference"))
  
  dialog = AdditionalNodesDialog(dummydata, dummytags)
  if dialog.exec_():
  print dialog.data()
  """
