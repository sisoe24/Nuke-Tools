# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import sys
import nuke
import pyui

__panels = dict()

def registerPanel( id, command ):
  __panels[id] = command

def unregisterPanel( id, command ):
  del __panels[id]

def restorePanel( id ):
  try:
    return __panels[id]()
  except:
    print("Can't restore panel '", id, "' because it hasn't been registered.")
    return None

def PythonPanelKnobChanged(widget):
  widget.knobChangedCallback(nuke.thisKnob())

class PythonPanel( pyui.Dialog ):

  def __init__( self, title = "", id = "", scrollable = True ):
    pyui.Dialog.__init__( self, title, id, scrollable )
    self.__node = nuke.PanelNode()
    self.__widget = None
    self.__openTabGroups = 0
    self.okButton = None
    self.cancelButton = None
    self._isModalDialog = False

  def addCallback( self ):
    nuke.addKnobChanged(PythonPanelKnobChanged, args = self, nodeClass = 'PanelNode', node = self.__node)

  def removeCallback( self ):
    nuke.removeKnobChanged(PythonPanelKnobChanged, args = self, nodeClass = 'PanelNode', node = self.__node)

  def addKnob( self, knob ):
    if type(knob) == nuke.BeginTabGroup_Knob:
      self.__openTabGroups += 1
    elif type(knob) == nuke.EndTabGroup_Knob:
      self.__openTabGroups -= 1
    elif type(knob) == nuke.Tab_Knob and self.__openTabGroups <= 0:
      self.addKnob( nuke.BeginTabGroup_Knob() )

    self.__node.addKnob( knob )
    knob.setFlag( nuke.NO_UNDO | nuke.NO_ANIMATION )

  def removeKnob( self, knob ):
    if type(knob) == nuke.BeginTabGroup_Knob:
      self.__openTabGroups -= 1
    elif type(knob) == nuke.EndTabGroup_Knob:
      self.__openTabGroups += 1

    self.__node.removeKnob( knob )

  def knobs( self ):
    return self.__node.knobs()

  def writeKnobs( self, flags ):
    return self.__node.writeKnobs( flags )

  def readKnobs( self, s ):
    return self.__node.readKnobs( s )

  def knobChangedCallback(self, knob):
    self.knobChanged(knob)
    if knob == self.okButton:
      self.finishModalDialog( True )
    elif knob == self.cancelButton:
      self.finishModalDialog( False )

  def knobChanged(self, knob):
    pass

  def finishModalDialog( self, result ):
    self.__modalResult = result
    self.hide();

  def ok( self ):
    self.finishModalDialog( True )

  def cancel( self ):
    self.finishModalDialog( False )

  def create( self ):
    while self.__openTabGroups > 0:
      self.addKnob(nuke.EndTabGroup_Knob())
    if self.__widget == None:
      self.__widget = self.__node.createWidget( self )
      self.add( self.__widget, 0, 0, 1, 3 )

  def show( self ):
    self.addCallback()
    self.create()
    super(PythonPanel, self).show()

  def hide( self ):
    super(PythonPanel, self).hide()

  def showModalDialog( self, defaultKnobText = "" ):
    self.__modalResult = None;
    self._isModalDialog = True
    if self.okButton == None:
      self._makeOkCancelButton()
    if defaultKnobText == "":
      defaultKnobText = self.okButton.name()
    self.showModal(defaultKnobText)
    return self.__modalResult

  def _makeOkCancelButton(self):
    while self.__openTabGroups > 0:
      self.addKnob(nuke.EndTabGroup_Knob())
    self.okButton = nuke.Script_Knob( "OK" )
    self.addKnob( self.okButton )
    self.okButton.setFlag( nuke.STARTLINE )
    self.cancelButton = nuke.Script_Knob( "Cancel" )
    self.addKnob( self.cancelButton )

  def showModal( self, defaultKnobText = "" ):
    self.addCallback()
    self.create()
    super(PythonPanel, self).showModal(defaultKnobText)
    self.removeCallback()

  def addToPane( self, pane = None ):
    self.create()
    if pane != None:
      pane.add( self )
    elif nuke.thisPane() != None:
      nuke.thisPane().add( self )
    self.addCallback()
    return self

  def accept(self):
    if self._isModalDialog:
      self.ok()

  def reject(self):
    if self._isModalDialog:
      self.cancel()


class WidgetKnob():
  def __init__(self, widget):
    self.widgetClass = widget

  def makeUI(self):
    self.widget = self.widgetClass()
    return self.widget

def registerWidgetAsPanel ( widget, name, id, create = False ):
  """registerWidgetAsPanel(widget, name, id, create) -> PythonPanel

    Wraps and registers a widget to be used in a Nuke panel.

    widget - should be a string of the class for the widget
    name - is is the name as it will appear on the Pane menu
    id - should the the unique ID for this widget panel
    create - if this is set to true a new NukePanel will be returned that wraps this widget

    Example ( using PySide2 )

    import nuke
    from PySide2 import QtCore, QtWidgets
    from nukescripts import panels

    class NukeTestWindow( QtWidgets.QWidget ):
      def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setLayout( QtWidgets.QVBoxLayout() )
        
        self.myTable = QtWidgets.QTableWidget()
        headers = ['Date', 'Files', 'Size', 'Path' ]
        self.myTable.setColumnCount( len( headers ) )
        self.myTable.setHorizontalHeaderLabels( headers )
        self.layout().addWidget( self.myTable )

    nukescripts.registerWidgetAsPanel('NukeTestWindow', 'NukeTestWindow', 'uk.co.thefoundry.NukeTestWindow' )
  """


  class Panel( PythonPanel ):

    def __init__(self, widget, name, id):
      PythonPanel.__init__(self, name, id )
      self.customKnob = nuke.PyCustom_Knob( name, "", "__import__('nukescripts').panels.WidgetKnob(" + widget + ")" )
      self.addKnob( self.customKnob  )

  def addPanel():
    return Panel( widget, name, id ).addToPane()

  menu = nuke.menu('Pane')
  menu.addCommand( name, addPanel)
  registerPanel( id, addPanel )

  if ( create ):
    return Panel( widget, name, id )
  else:
    return None


