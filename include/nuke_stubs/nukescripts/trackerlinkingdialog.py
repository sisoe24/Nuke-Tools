import nuke
import nukescripts

##############################################################################
# A quick-n-dirty storage of "last values" for knobs that we want to appear
# with the value they were assigned the last time the dialog was open during
# this GUI session.

_gLastState = {}
_gTrackExpression = ["",""]

def _getLastState( knob, defaultValue=None ):
  """Return the given knob's stored last state value.
  If none exists, defaultValue is returned.
  Values are stored in a dict referenced by knob name, so names must be unique!"""
  global _gLastState
  if knob.name() in _gLastState:
    return _gLastState[knob.name()]
  else:
    return defaultValue

def _setLastState( knob ):
  """Store the knob's current value as the 'last state' for the next time the dialog is opened.
  Values are stored in a dict referenced by knob name, so names must be unique!"""
  global _gLastState
  _gLastState[knob.name()] = knob.value()


##############################################################################
# LinkToTrack Panel
# This panel offers the user a selection of Tracker nodes in the project and
# returns an expression referencing either the Tracker's 'translate' knob or
# computing the average value of the selected track points on the node.

class LinkToTrackPanel( nukescripts.PythonPanel ):
  def __init__( self, groupContext ):
    nukescripts.PythonPanel.__init__( self, "Link to Tracker", "uk.co.thefoundry.LinkToTrackPanel" )

    # Initialising return variable
    global _gTrackExpression
    _gTrackExpression = ["",""]

    # Show a list of trackers in the project.
    self._trackers = []
    with nuke.toNode(groupContext):
      for n in nuke.allNodes():
        if n.linkableKnobs(nuke.KnobType.eXYKnob):
          self._trackers.append( n.name() )
    self._tracker = nuke.Enumeration_Knob( "trackers", "tracker node", self._trackers )
    self._tracker.setTooltip( "The Tracker node to link to." )
    self._tracker.setValue( _getLastState( self._tracker, self._trackers[0] ) )
    self.addKnob( self._tracker )

    # Choice of linking to the translate on the tracker or to track point positions.
    self._link_to = nuke.Enumeration_Knob( "link_to", "link to", ["position", "translate", "translate as offset"] )
    self._link_to.setValue( _getLastState( self._link_to, 'translate' ) )
    self._link_to.setTooltip( "Choose whether to link to the translation computed in the Tracker's Transform tab or to a specific track point position. If multiple track points are chosen they will be averaged." )
    self.addKnob( self._link_to )
    self._link_to.setFlag( nuke.ENDLINE )

    # Creating all of the linkable knobs for all trackers in advance, then
    # going to hide / show them based on the visibility below.
    self._all_linkables = {}
    for tracker in self._trackers:
      n = nuke.toNode(tracker)
      self._all_linkables[tracker] = []
      l = n.linkableKnobs(nuke.KnobType.eXYKnob)
      for i in range(len(l)):
        # Removing any translate links as they are serviced by the "link" enum above.
        if l[i].knob().name() == "translate":
          continue
        if len(l[i].displayName()) > 0:
          knobname = l[i].displayName()
          exprname = "tracks." + str(i-1)
        else:
          knobname = l[i].knob().name()
          exprname = knobname
        point = nuke.Boolean_Knob( exprname, knobname )
        point.setTooltip( "Use this track point when linking to 'position'." )
        point.setVisible(False)
        self.addKnob( point )
        self._all_linkables[tracker].append(point)

    # Show the expression that's going to set in case user wants to tweak or
    # copy it before closing the dialog.
    self._expressionX = nuke.EvalString_Knob( "expression.x" )
    self._expressionX.setTooltip( "This is the expression that will be applied to the x position. You can edit it before closing the dialog but changing settings on this panel will rebuild it, losing your changes." )
    self.addKnob( self._expressionX )
    self._expressionY = nuke.EvalString_Knob( "expression.y" )
    self._expressionY.setTooltip( "This is the expression that will be applied to the y position. You can edit it before closing the dialog but changing settings on this panel will rebuild it, losing your changes." )
    self.addKnob( self._expressionY )

    # Set up knobs and linkable objects
    self._updateEverything()


  def _updateEverything(self):
    self._updateLinkableKnobInfo()

    self._updateExpression()

  def _updateLinkableKnobInfo(self):
    use_points = ( self._link_to.value() == 'position' )

    for tracker in self._trackers:
      for point in self._all_linkables[tracker]:
        point.setEnabled( use_points )
        point.setVisible(False)

    firstTrack = 1
    self._track_points = []
    for point in self._all_linkables[self._tracker.value()]:
      point.setValue( _getLastState( point, (firstTrack==1) ) )
      point.setVisible(True)
      self._track_points.append(point)
      firstTrack = 0

  def _updatePointsEnabled(self):
    # Display check boxes for selection of which track points should be linked.
    # If more than one is selected the expression is set to average them.
    """Enable the track point bools when linking to position; disable otherwise."""
    #use_points = ( self._link_to.value() == 'position' )
    #for point in self._track_points:
    #  point.setEnabled( use_points )


  def _updateExpression(self):
    """Update the expression to reflect the current settings."""
    if self._link_to.value() == 'translate':
      self._expressionX.setValue( self._tracker.value() + ".translate.x" )
      self._expressionY.setValue( self._tracker.value() + ".translate.y" )
    elif self._link_to.value() == 'translate as offset':
      self._expressionX.setValue( "curve + " + self._tracker.value() + ".translate.x" )
      self._expressionY.setValue( "curve + " + self._tracker.value() + ".translate.y" )
    else:
      pointCount = 0
      exprX = " + ".join([self._tracker.value() + "." + point.name() + ".track_x" for point in self._track_points if point.value()])
      exprY = " + ".join([self._tracker.value() + "." + point.name() + ".track_y" for point in self._track_points if point.value()])
      pointCount = sum( (1 for point in self._track_points if point.value()) )
      if pointCount > 1:
        exprX = "(" + exprX + ")/" + str(pointCount)
        exprY = "(" + exprY + ")/" + str(pointCount)
      self._expressionX.setValue( exprX )
      self._expressionY.setValue( exprY )

  def knobChanged( self, knob ):
    _setLastState( knob )

    # If expression changes, don't try to update and possibly trash it.
    if knob == self._expressionX or knob == self._expressionY:
      return

    self._updateExpression()
    if knob == self._link_to or knob == self._tracker:
      global _gLastTracker
      _gLastTracker = knob.value()
      self._updateEverything()

  def addToPane( self ):
    nukescripts.PythonPanel.addToPane( self, pane=nuke.thisPane() )



def trackerlinkingdialog(groupContext):
  d = LinkToTrackPanel(groupContext)
  if d.showModalDialog() == True:
    global _gTrackExpression
    _gTrackExpression = [d._expressionX.value(), d._expressionY.value()]
    return [d._expressionX.value(), d._expressionY.value()]

def trackerlinkingdialogexpressionx():
  return _gTrackExpression[0]

def trackerlinkingdialogexpressiony():
  return _gTrackExpression[1]
