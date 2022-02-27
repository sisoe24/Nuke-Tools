# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.
import nuke
import nukescripts

class FrameRangePanel( nukescripts.PythonPanel ):
  """class that creates a Python panel for editing frame ranges"""

  def __init__( self, initalStart, initialEnd ):
    """Constructor that takes 2 arguments for the initial start and end frame numbers"""

    nukescripts.PythonPanel.__init__( self, "Set frame range", "uk.co.thefoundry.FramePanel" )
    self.fromFrame = nuke.Int_Knob( "fromFrame", "from:" )
    self.addKnob( self.fromFrame )
    self.fromFrame.setValue( int(initalStart) )
    self.toFrame = nuke.Int_Knob( "toFrame", "to:" )
    self.addKnob( self.toFrame )
    self.toFrame.setValue( int(initialEnd) )
  def showDialog( self ):
    """show panel dialog, returns if accept was pressed"""
    return nukescripts.PythonPanel.showModalDialog( self )
