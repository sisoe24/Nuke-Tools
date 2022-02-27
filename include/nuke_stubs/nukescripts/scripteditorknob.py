import nuke
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QWidget,
                               QSplitter,
                               QVBoxLayout)
from .blinkscripteditor import *

class ScriptEditor(QWidget):

  doNotUpdate = False

  def __init__(self, knob, parent=None):
    super(ScriptEditor, self).__init__(parent)

    self.knob = knob
    #doNotUpdate is used to prevent circular updates when a user enters text.
    self.doNotUpdate = False

    #Set title
    self.setWindowTitle("BlinkScript Editor")

    #Make splitter
    splitter = QSplitter(Qt.Vertical)

    #Setup main layout
    self.myTextWindow = ScriptInputArea(None, self, self)
    splitter.addWidget(self.myTextWindow)

    layout = QVBoxLayout()
    self.setLayout(layout)
    layout.addWidget(splitter)

    #Update the stored text on the knob when the user changes it
    self.myTextWindow.userChangedEvent.connect(self.storeTextOnKnob)

  def printText(self):
    data = self.myTextWindow.toPlainText()
    print(str(data))

  def getText(self):
    data = self.myTextWindow.toPlainText()
    return data

  def storeTextOnKnob(self):
    self.doNotUpdate = True
    self.knob.setText(self.myTextWindow.toPlainText())

  def updateValue(self):
    #Update the UI text from the knob
    if not self.doNotUpdate:
      self.myTextWindow.setPlainText(self.knob.getText())
    self.doNotUpdate = False
    # knob value changed
    pass

class ScriptEditorWidgetKnob():
  def __init__(self, knob):
    self.knob = knob

  def makeUI(self):
    return ScriptEditor(self.knob)


def makeScriptEditorKnob():
  return ScriptEditorWidgetKnob(nuke.thisKnob())

