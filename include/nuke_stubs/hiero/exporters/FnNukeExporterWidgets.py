from PySide2 import(QtCore, QtGui, QtWidgets)

class NukeProjectNodeSelectionWidget(QtWidgets.QWidget):
  kReadNode = 0
  kWriteNode = 1
  kAnnotationsNode = 2

  kMinimumHeight = 50
  kWidth = 200

  def __init__(self, exportTemplate, preset):
    QtWidgets.QWidget.__init__(self)
    self._exportTemplate = exportTemplate
    self._preset = preset
    self._list = []
    self._model = []
    self.initUI()


  def nodeSelectionChanged(self, index):
    self._stackedWidget.setCurrentIndex(index)


  def getModel(self, model):
    return self._model[model]


  def initUI(self):
    #Initialize layout
    nodeSelectionLayout = QtWidgets.QVBoxLayout(self)
    nodeSelectionLayout.setContentsMargins(0,0,0,0);

    containerWidget = QtWidgets.QWidget()
    nodeSelectionLayout.addWidget(containerWidget)

    self._nodeSelectionComboBox = QtWidgets.QComboBox()
    self._nodeSelectionComboBox.currentIndexChanged.connect(self.nodeSelectionChanged)
    self._nodeSelectionComboBox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
    comboBoxLayout = QtWidgets.QHBoxLayout(containerWidget)
    comboBoxLayout.setContentsMargins(0,0,0,0);
    comboBoxLayout.addWidget(self._nodeSelectionComboBox)
    comboBoxLayout.addStretch()


    self._stackedWidget = QtWidgets.QStackedWidget()
    nodeSelectionLayout.addWidget(self._stackedWidget)


  def addNodeSelector(self, id, name, propertyName, tooltip, select = False)  :
    self._nodeSelectionComboBox.addItem(name)
    listView = QtWidgets.QListView()
    listView.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
    self._list.insert(id, listView)
    self._model.insert(id, QtGui.QStandardItemModel())

    model = self._model[id]
    properties = self._preset.properties()
    usedPaths = set()
    # Default to the empty item unless the preset has a value set.
    for path, preset in self._exportTemplate.flatten():

      if preset is self._preset:
        continue

      if id is self.kWriteNode:
        if not hasattr(preset._parentType, 'nukeWriteNode'):
          continue

      # Duplicated paths are now allowed in export presets, but: we have no
      # useful way of allowing the user to select one item with a given path
      # but not the other. Only show the path once, and if there are e.g. 2
      # write nodes with the same path, they'll both be included.
      if path in usedPaths:
        continue

      usedPaths.add(path)

      item = QtGui.QStandardItem(path)
      item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)

      item.setData(QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)
      if path in properties[propertyName]:
        item.setData(QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)

      model.appendRow(item)

    self._list[id].setModel(self._model[id])
    self._list[id].setToolTip(tooltip)
    self._stackedWidget.addWidget(self._list[id])
    if select:
      self._nodeSelectionComboBox.setCurrentIndex(self._nodeSelectionComboBox.count()-1)


class TimelineWriteNodeWidget(QtWidgets.QWidget):
  timelineWriteNodeChanged = QtCore.Signal(str)

  def __init__(self, model, preset):
    QtWidgets.QWidget.__init__(self)
    self.initUI()
    hasItemsToSelect = False
    self._preset = preset
    self._model = model
    self._model.dataChanged.connect(self.dataModelChanged)
    self._comboboxModel = QtGui.QStandardItemModel()
    self._writeNodeComboBox.setModel(self._comboboxModel)
    timelineWriteNode = self._preset.properties()["timelineWriteNode"]
    didSetMainNode = False
    #copy the model from the nodeSelector
    for currentItem in range(0,self._model.rowCount()):
      currentIndex = self._model.index(currentItem,0)
      item = self._model.item(currentItem)
      currentPath = self._model.data(currentIndex, QtCore.Qt.DisplayRole)
      isIncluded = self._model.data(currentIndex, QtCore.Qt.CheckStateRole)
      #create new Item, initialize and append to model for combobox
      newItem = QtGui.QStandardItem(currentPath)
      newItem.setEnabled(isIncluded)
      self._comboboxModel.appendRow(newItem)
      #if it's the default, select it
      if timelineWriteNode == currentPath:
        self._writeNodeComboBox.setCurrentIndex(currentItem)
        didSetMainNode = True

    if not didSetMainNode:
      self.updateCurrentSelection()


  def timelineNodeChanged(self, text):
    self.timelineWriteNodeChanged.emit(text)


  def indexChanged(self):
    text = self._writeNodeComboBox.currentText()
    self.timelineNodeChanged(text)


  def initUI(self):
    mainLayout = QtWidgets.QVBoxLayout(self)
    mainLayout.setContentsMargins(0,0,0,0);
    self._writeNodeComboBox = QtWidgets.QComboBox()
    self._writeNodeComboBox.currentIndexChanged.connect(self.indexChanged)
    mainLayout.addWidget(self._writeNodeComboBox)


  def getFirstAvailableItem(self):
    for currentItem in range(0,self._comboboxModel.rowCount()):
      item = self._comboboxModel.item(currentItem)
      enabled = item.isEnabled()
      if item.isEnabled():
        return currentItem
    return -1


  def updateCurrentSelection(self):
    nextItem = self.getFirstAvailableItem()
    if nextItem >=0:
      #if we found a selectible item, enable the widget
      self._writeNodeComboBox.setEnabled(True)
      self._writeNodeComboBox.setCurrentIndex(nextItem)
    else:
      #if none could be found, disable the menu
      self._writeNodeComboBox.setEnabled(False)
      self.timelineNodeChanged("")


  def dataModelChanged(self, topLeft, bottomRight):
    #a writeNode was included/excluded to the script
    isIncluded = self._model.data(topLeft, QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked
    #get corresponding item in selector model
    item = self._comboboxModel.item(topLeft.row())
    #enable/disable on our combo box
    item.setEnabled(isIncluded)

    currentItemIsSelected = self._writeNodeComboBox.currentIndex() == topLeft.row()

    #if the write node was removed from the script and it was the default one,
    #select the first one in the list
    if (not isIncluded and currentItemIsSelected) or not self._writeNodeComboBox.isEnabled():
      self.updateCurrentSelection()
