"""
Code for layout of exported Nuke scripts.
"""

import hiero.core
import hiero.core.nuke as _nuke
from PySide2.QtCore import QRect, Qt
from PySide2.QtGui import QFont, QFontMetrics
import itertools


class LayoutBase(object):
  """ Base class for layouts.  Each layout context should have an associated layout class with
      appropriate behaviour.  This base class contains helper functions and a default layout
      implementation, with some customisation through members set on the object. """

  # Flags for specifying alignment behavior
  kAlignLeft = 0
  kAlignCenter = 1

  def __init__(self, script, layoutContext):
    """ Initialise with a script writer and layout context.  Iterates over child contexts
        and creates sub-layouts. """

    # Parameters for layout.  Sub-classes can set these to customise the default behaviour.
    self.nodeSpacing = 20
    self.childLayoutSpacing = 50
    self.shouldCreateBackdrop = True
    self.backdropColor = None
    self.backdropLabelFontSize = 42
    self.leftMargin = 60
    self.topMargin = 40
    self.rightMargin = 60
    self.bottomMargin = 40

    self.rect = None
    self.script = script
    self.layoutContext = layoutContext
    self.childLayouts = []

    # Loop over child contexts and create layouts for them.
    for childContext in layoutContext.getChildren():
      if layoutContext.getChildren() or layoutContext.getNodes():
        layoutClass = _layoutsDict[childContext.getType()]
        assert layoutClass, "No layout for context: %s %s" % (childContext.getType(), childContext.getName())
        childLayout = layoutClass(script, childContext)
        self.childLayouts.append(childLayout)


  def getLayoutWidth(self):
    """ Determine the width of the layout.  This can be done without actually determining the position
        of anything, and is required for determining the height of backdrop labels. """
    width = 0

    # Determine child layout widths
    if self.childLayouts:
      for childLayout in self.childLayouts:
        childWidth = childLayout.getLayoutWidth()
        width += childWidth
      width += self.childLayoutSpacing * len(self.childLayouts)-1

    nodeMaxW = 0
    for node in self.layoutContext.getNodes():
      nodeW, nodeH = node.getNodeSize()
      nodeMaxW = max(nodeW, nodeMaxW)
      width = max(width, nodeW)

    if self.shouldCreateBackdrop:
      width += self.leftMargin + self.rightMargin

    return width


  def getBackdropLabelHeight(self, label, width):
    """ Get the height of the backdrop label for the given width. """

    # Creating a QFont with no argument selects a default font family.  This is what the Nuke code
    # does if no font is specified, so we should end up with the same font.
    font = QFont()
    font.setPixelSize(self.backdropLabelFontSize)
    metrics = QFontMetrics(font)
    # For the layout we're requesting, Qt doesn't care about the rect height, so pass 1.
    # Specify wrap anywhere as that's what the Nuke text layout does.
    rect = metrics.boundingRect(0, 0, width, 1, Qt.TextWrapAnywhere, label)
    return rect.height()


  def layoutChildContexts(self, layouts, xpos, ypos, zorder):
    """ Layout child contexts with the given orientation, starting from (xpos, ypos).  Returns the bounding rect. """
    rect = QRect(xpos, ypos, 1, 1)

    # Increment the z order if this layout creates a backdrop
    childZOrder = zorder+1 if self.shouldCreateBackdrop else zorder

    for childLayout in layouts:
      childNodes = childLayout.layoutContext.getNodes()

      childRect = childLayout.doLayout(xpos, ypos, childZOrder)
      xpos = childRect.right() + self.childLayoutSpacing

      rect |= childRect

    return rect


  def layoutNodes(self, nodes, xpos, ypos, alignment):
    """ Layout child nodes with the given alignment to the xpos.  Returns the bounding rect."""
    rect = QRect(xpos, ypos, 1, 1)

    for node in nodes:

      # Merge/Dissolve nodes for connecting clips in a track should never be higher than their A input
      if isinstance(node, _nuke.MergeNode) or isinstance(node, _nuke.DissolveNode):
        if node.inputNodes():
          inpux, inputy = node.inputNodes()[0].getPosition()
          if ypos < inputy:
            ypos = inputy

      xpos, ypos = self.layoutNode(node, xpos, ypos, alignment, rect)

    return rect

  def alignmentForNodesLayout(self, left):
    """ Get the position and alignment flag for the horizontal positioning of
    nodes. By default aligns to the left border argument. """
    return left + self.leftMargin, LayoutBase.kAlignLeft

  def layoutNode(self, node, xpos, ypos, alignment, rect):
    """ Layout nodes vertically, with the given alignment to the xpos.  Returns the bounding rect.  If the
        node has been set to align to another node, will attempt to align them horizontally. """
    nodeW, nodeH = node.getNodeSize()

    ypos += node.getTopSpacing()

    # Check if the node should align to another node, and if so set the y so they are
    # horizontally aligned through the center.
    alignToNode = node.getAlignToNode()
    if alignToNode:
      alignToNodeX, alignToNodeY = alignToNode.getPosition()
      if alignToNodeX is not None and alignToNodeY is not None:

        alignToNodeW, alignToNodeH = alignToNode.getNodeSize()

        if node.getNodeAlignment() is _nuke.Node.kNodeAlignY:
          xpos = alignToNodeX + alignToNodeW + nodeW + node.getAlignmentOffsetX()
          ypos = alignToNodeY + node.getAlignmentOffsetY()
        else:
          xpos = alignToNodeX + node.getAlignmentOffsetX()
          ypos = alignToNodeY + alignToNodeH + nodeH + node.getAlignmentOffsetY()

    # Don't include Dot nodes in the rect calculations. Their layout is corrected once
    # all dependent nodes are properly laid out, and may or may not be contained in the
    # backdrop, depending upon what they are connecting
    isDot = isinstance(node, _nuke.DotNode)
    if alignment == LayoutBase.kAlignLeft:
      node.setPosition(xpos, ypos)
      if not isDot:
        rect.setRight( max(rect.right(), xpos + nodeW) )
    else: # kAlignCenter
      nodeX = xpos - (nodeW / 2)
      node.setPosition(nodeX, ypos)
      if not isDot:
        rect.setLeft( min(rect.left(), nodeX) )
        rect.setRight( max(rect.right(), nodeX + nodeW) )

    if not isDot:
      rect.setBottom( max(rect.bottom(), ypos + nodeH) )

    ypos += nodeH + self.nodeSpacing

    if node.inputNodes():
      input0 = node.inputNodes()[0]
      if isinstance(input0, _nuke.DotNode):
        input0.align(input0.inputNodes()[0], node)

    return xpos, ypos

  def createBackdrop(self, color, rect, label, zorder):
    """ Create a backdrop node, and add it to the script. """
    backdrop = _nuke.BackdropNode(rect.x(), rect.y(), rect.width(), rect.height())
    backdrop.setLabelFontSize(self.backdropLabelFontSize)
    if color:
      backdrop.setColor(color)
    backdrop.setLabel(label)
    backdrop.setZOrder(zorder)
    self.script.addNode(backdrop)


  def doLayout(self, xpos, ypos, zorder):
    """ Perform layout, and return the bounding rect.  This default implementation lays out child layouts horizontally,
        and then arranges nodes below them vertically. """

    self.rect = QRect(xpos, ypos, 1, 1)

    xpos += self.leftMargin
    ypos += self.topMargin

    # If creating a backdrop, include the height of the label
    if self.shouldCreateBackdrop:
      ypos += self.getBackdropLabelHeight(self.layoutContext.getLabel(), self.getLayoutWidth())

    if self.childLayouts:
      childContextsRect = self.layoutChildContexts(self.childLayouts, xpos, ypos, zorder)
      self.rect |= childContextsRect
      ypos = childContextsRect.bottom() + self.childLayoutSpacing

    xpos, align = self.alignmentForNodesLayout(xpos)
    nodesRect = self.layoutNodes(self.layoutContext.getNodes(), xpos, ypos, align)
    self.rect |= nodesRect

    self.rect.adjust( 0, 0, self.rightMargin, self.bottomMargin )

    if self.shouldCreateBackdrop:
      self.createBackdrop(self.backdropColor, self.rect, self.layoutContext.getLabel(), zorder)

    return self.rect


  def getAlignHint(self):
    """ Get x and y positions to align to.  If the layout has nodes, it will return the
        center of the last node, otherwise it will return the align hint of the last child layout. """
    nodes = self.layoutContext.getNodes()
    if nodes:
      alignToNode = nodes[-1]
      nodeX, nodeY = alignToNode.getPosition()
      nodeW, nodeH = alignToNode.getNodeSize()
      return nodeX + (nodeW/2), nodeY + (nodeH/2)
    elif self.childLayouts:
      if self.childLayouts[-1] is not None:
        return self.childLayouts[-1].getAlignHint()

    # Fallback to the self.rect
    if self.rect is None:
      return 0, 0

    center = self.rect.center()
    return center.x(), center.y()


class TracksLayout(LayoutBase):
  """ Class for laying out a list of tracks. This is currently just used for the ViewLayout """

  def __init__(self, script, layoutContext):
    super(TracksLayout, self).__init__(script, layoutContext)

    self.shouldCreateBackdrop = False
    self.leftMargin = 0
    self.topMargin = 0
    self.rightMargin = 0
    self.bottomMargin = 0

    self.alignToTrackLayout = None

    # Check if the sequence is disconnected, so we can figure out which track layout is going to
    # be the output and set the alignment hint accordingly.
    self.disconnectedLayout = layoutContext.getData("disconnected")

    def _layoutSort(layout):
      track = layout.layoutContext.getData("track")
      if track:
        return -track.trackIndex()
      else:
        return 0

    # The track layouts might not be in the right order, sort them highest to lowest
    self.childLayouts.sort(key=_layoutSort)

    # For a disconnected layout, effects/annotations tracks which are connected are arranged vertically below the output track.
    # Build separate lists, otherwise everything is laid out horizontally
    self.verticalTrackLayouts = []
    self.horizontalTrackLayouts = []
    if self.disconnectedLayout:
      for layout in self.childLayouts:
        if layout.subTrackItemsOnly() and not layout.layoutContext.getData("disconnected"):
          self.verticalTrackLayouts.append(layout)
        else:
          self.horizontalTrackLayouts.append(layout)
    else:
      self.horizontalTrackLayouts = self.childLayouts

  def getLayoutWidth(self):
    """ Determine the width of the layout.  This can be done without actually determining the position
        of anything, and is required for determining the height of backdrop labels. """
    width = 0

    # Determine child layout widths
    if self.horizontalTrackLayouts:
      for childLayout in self.horizontalTrackLayouts:
        width += childLayout.getLayoutWidth()
      width += self.childLayoutSpacing * len(self.childLayouts)-1
    else:
      for childLayout in self.verticalTrackLayouts:
        width = max(width, childLayout.getLayoutWidth())

    for node in self.layoutContext.getNodes():
      nodeW, nodeH = node.getNodeSize()
      if nodeW is not None:
        width = max(width, nodeW)

    if self.shouldCreateBackdrop:
      width += self.leftMargin + self.rightMargin

    return width

  def doLayout(self, xpos, ypos, zorder):
    """ Layout the sequence.  Lays out tracks horizontally, except tracks that only have soft effects or annotations, which
        are laid out vertically underneath. """

    self.rect = QRect(xpos, ypos, 1, 1)

    xpos += self.leftMargin
    ypos += self.topMargin

    # If creating a backdrop, include the height of the label
    if self.shouldCreateBackdrop:
      ypos += self.getBackdropLabelHeight(self.layoutContext.getLabel(), self.getLayoutWidth())

   #Each track has a horizontal part and a vertical part which need to be drawn in the correct order.
   # First we draw all of the horizontal parts starting from the left across to the right.
   # Then we draw the vertical parts starting from the top along the righthand edge (Which is under the main track)

    merges = []
    tracks = []

    #First get the list of merge layouts each will have a parent track
    for childLayout in self.childLayouts:
      isMergeLayout = isinstance(childLayout, MergeLayout)
      if isMergeLayout :
        merges.append(childLayout)


    for childLayout in self.childLayouts:
      isTrackLayout = isinstance(childLayout, TrackLayout)
      if isTrackLayout :
        tracks.append(childLayout)

        for layout in merges:
          if childLayout.getTrackName() == layout.getInputA():
            # Assume that each track is only the A input for one merge
            childLayout.setMerge(layout)

    # Now do the laying out
    yMain = ypos
    xHorizontal = xpos
    yVertical = ypos

    horzontalRect = QRect(xHorizontal, yMain, 0, 0)
    verticalRect = QRect(xHorizontal, yMain, 0, 0)

    # Now iterate just the tracks in order and draw the horizontal parts of the tracks
    for track in tracks:
      horzontalRect |= track.layoutHorizontal( xHorizontal, yMain, zorder)
      xHorizontal = horzontalRect.right() + self.childLayoutSpacing

    self.rect = horzontalRect
    # We want to line the vertical tracks up with the last horizontal track.
    # This should have been layed out above.
    xAlignLast, yAlignLast = tracks[-1].getAlignHint()

    # Now iterate just the tracks in order and draw the vertical parts of the tracks
    yVertical = horzontalRect.bottom() + self.childLayoutSpacing

    # Ordering is opposite the the order of the horizontal tracks
    for track in reversed(tracks):
      xHorizontal = xAlignLast - ( track.getLayoutWidth() / 2 )
      verticalRect |= track.layoutVertical( xHorizontal, yVertical, zorder)
      yVertical = verticalRect.bottom() + self.childLayoutSpacing
      xAlignLast, yAlignLast = track.getVerticalLayoutAlignHint()

      # We want our align hint to align to the final non disconnected track
      if not track.layoutContext.getData("disconnected"):
        self.alignToTrackLayout = track

    self.rect |= verticalRect

    xpos = horzontalRect.bottom() + self.childLayoutSpacing

    nodesRect = self.layoutNodes(self.layoutContext.getNodes(), xpos, ypos, LayoutBase.kAlignLeft)
    self.rect |= nodesRect
    self.rect.adjust( 0, 0, self.rightMargin, self.bottomMargin )

    if self.shouldCreateBackdrop:
      self.createBackdrop(self.backdropColor, self.rect, self.layoutContext.getLabel(), zorder)

    return self.rect

  def getAlignHint(self):
    # If we've set a specific TrackLayout to align to then return the align hint for that.
    # Note that we will always want to align with the vertical part of the TrackLayout
    if self.alignToTrackLayout:
      return self.alignToTrackLayout.getVerticalLayoutAlignHint()

    # If the sequence is disconnected, align to the first layout (which is the top track),
    # that's where the output to the write node comes from
    for layout in self.horizontalTrackLayouts:
      disconnected = layout.layoutContext.getData("disconnected")
      if not disconnected and not layout.subTrackItemsOnly():
        return layout.getAlignHint()

    return super(TracksLayout, self).getAlignHint()


class ViewLayout(TracksLayout):
  """ Used for laying out the views for a sequence separately. """
  def __init__(self, script, layoutContext):
    super(ViewLayout, self).__init__(script, layoutContext)


class SequenceLayout(LayoutBase):
  def __init__(self, script, layoutContext):
    super(SequenceLayout, self).__init__(script, layoutContext)
    self.shouldCreateBackdrop = False
    self.leftMargin = 0
    self.topMargin = 0
    self.rightMargin = 0
    self.bottomMargin = 0

  def alignmentForNodesLayout(self, left):
    """ Override. Align to the last child layout. """
    return self.childLayouts[-1].getAlignHint()[0], LayoutBase.kAlignCenter


class TrackLayout(LayoutBase):
  """ Track level layout. """

  def __init__(self, script, layoutContext):
    super(TrackLayout, self).__init__(script, layoutContext)
    self.backdropColor = "0xa04040ff"

    #The merge for integrating this track into the main branch
    # Assume we only have one
    self._mergeLayout = None

  def getVerticalLayoutAlignHint(self):
    if self._mergeLayout:
      return self._mergeLayout.getAlignHint()
    return self.getAlignHint()

  def setMerge(self, merge):
    self._mergeLayout = merge

  def layoutVertical(self, xpos, ypos, zorder):
    if self._mergeLayout:
      return self._mergeLayout.doLayout(xpos, ypos, zorder)
    return QRect(xpos, ypos, 0, 0)

  def layoutHorizontal(self, xpos, ypos, zorder):
    return self.doLayout(xpos, ypos, zorder)

  def subTrackItemsOnly(self):
    """ Get if the track being laid out only has sub-track items (i.e. effects and annotations) on it. """
    track = self.layoutContext.getData("track")

    if track is None:
      return False

    if list(track.items()):
      return False

    return True

  def getTrackName(self):
    return self.layoutContext.getData("track")


  def doLayout(self, xpos, ypos, zorder):
    """ Do the track layout.  Reimplemented as the node layout is a bit different to the default. """

    self.rect = QRect(xpos, ypos, 1, 1)

    if not self.childLayouts and not self.layoutContext.getNodes():
      return self.rect

    xpos += self.leftMargin
    ypos += self.topMargin
    ypos += self.getBackdropLabelHeight(self.layoutContext.getLabel(), self.getLayoutWidth())

    if self.childLayouts:
      childContextsRect = self.layoutChildContexts(self.childLayouts, xpos, ypos, zorder)

      #Make sure we keep the margin on the left side of the child rect
      self.rect.setLeft(childContextsRect.left() - self.leftMargin)
      self.rect.setRight(childContextsRect.right() )

      self.rect |= childContextsRect

      alignToLayout = self.childLayouts[-1]

      ypos = alignToLayout.rect.bottom() + self.nodeSpacing

      # Align nodes to the center of the last child layout
      alignToNode = alignToLayout.layoutContext.getNodes()[-1]

      # Align to the last node in the layout.  Nodes should have a position and size by this point, but to
      # be safe check and fall back to the center of the the layout's rect
      alignToNodeX = alignToNode.getPosition()[0]
      alignToNodeW = alignToNode.getNodeSize()[0]
      if alignToNodeX is not None and alignToNodeW is not None:
        nodeAlignX = alignToNodeX + (alignToNodeW / 2)
      else:
        nodeAlignX = alignToLayout.rect.center().x()

      nodesRect = self.layoutNodes(self.layoutContext.getNodes(), nodeAlignX, ypos, LayoutBase.kAlignCenter)
    # No child layouts on the track, this occurs if the track only has effects/annotations
    else:
      nodesRect = self.layoutNodes(self.layoutContext.getNodes(), xpos, ypos, LayoutBase.kAlignLeft)
      self.rect.setLeft(nodesRect.left() - self.leftMargin)
      self.rect.setRight(nodesRect.right() )

    self.rect |= nodesRect

    self.rect.adjust( 0, 0, self.rightMargin, self.bottomMargin )

    self.createBackdrop(self.backdropColor, self.rect, self.layoutContext.getLabel(), zorder)

    return self.rect



class ClipLayout(LayoutBase):
  """ Clip layout. """

  def __init__(self, script, layoutContext):
    super(ClipLayout, self).__init__(script, layoutContext)
    self.backdropColor = "0xa09797ff"
    self.leftMargin = 80
    self.rightMargin = 80
    self.bottomMargin = 20

    # Separate the constant nodes and clip-related nodes
    self.clipNodes = []
    self.constantNodes = []
    for node in self.layoutContext.getNodes():
      if isinstance(node, _nuke.ConstantNode):
        self.constantNodes.append(node)
      else:
        self.clipNodes.append(node)


  def getLayoutWidth(self):
    width = 0

    # Determine child layout widths
    if self.childLayouts:
      for childLayout in self.childLayouts:
        width += childLayout.getLayoutWidth()
      width += self.childLayoutSpacing * len(self.childLayouts)-1

    if self.constantNodes:
      width += self.constantNodes[0].getNodeSize()[0]
      width += self.nodeSpacing

    nodeMaxW = 0
    for node in self.layoutContext.getNodes():
      nodeW, nodeH = node.getNodeSize()
      nodeMaxW = max(nodeMaxW, nodeW)
    width += nodeMaxW

    if self.shouldCreateBackdrop:
      width += self.leftMargin + self.rightMargin

    return width


  def doLayout(self, xpos, ypos, zorder):
    """ Perform layout, and return the bounding rect.  Lays out nodes in two columns, with constant nodes
        (for gaps in the timeline) on the left. """

    self.rect = QRect(xpos, ypos, 1, 1)

    xpos += self.leftMargin
    ypos += self.topMargin

    # If creating a backdrop, include the height of the label
    if self.shouldCreateBackdrop:
      ypos += self.getBackdropLabelHeight(self.layoutContext.getLabel(), self.getLayoutWidth())

    if self.constantNodes:
      mainNodesXPos = xpos + 80 + self.nodeSpacing
      mainNodesRect = self.layoutNodes(self.clipNodes, mainNodesXPos, ypos, LayoutBase.kAlignLeft)

      constNodesXPos = xpos
      constNodesRect = self.layoutNodes(self.constantNodes, constNodesXPos, ypos, LayoutBase.kAlignLeft)

      combinedRect = mainNodesRect | constNodesRect

      self.rect.setLeft(combinedRect.left() - self.leftMargin)
      self.rect.setRight(combinedRect.right())
      self.rect |= combinedRect

    else:
      nodesRect = self.layoutNodes(self.clipNodes, xpos, ypos, LayoutBase.kAlignLeft)

      self.rect.setLeft(nodesRect.left() - self.leftMargin)
      self.rect.setRight(nodesRect.right())

      self.rect |= nodesRect


    self.rect.adjust( 0, 0, self.rightMargin, self.bottomMargin )

    if self.shouldCreateBackdrop:
      self.createBackdrop(self.backdropColor, self.rect, self.layoutContext.getLabel(), zorder)

    return self.rect



class WriteLayout(TrackLayout):
  """ Layout for the write and associated nodes. """

  def __init__(self, script, layoutContext):
    super(WriteLayout, self).__init__(script, layoutContext)
    self.backdropColor = "0xa04040ff"
    self.leftMargin = 150
    self.rightMargin = 150


  def layoutNodes(self, nodes, xpos, ypos, alignment):
    # The timeline write and associated nodes will be positions on the main branch of the node graph

    # Additional writes will be positioned on new branches which are to the right of the main branch.
    # These branches will start with a dot node and end with the write node itself.
    # There may be additional nodes beteen the dot and the write which are associated with a particular write.

    rect = QRect(xpos, ypos, 0, 0)

    reachedFirstBranch = False
    dotY = ypos
    mainBranchX = xpos
    lastBranchX = xpos
    mainBranchY = ypos

    onBranch = False

    branchNodeW = 0
    branchNodeH = 0

    for node in nodes:
      nodeW, nodeH = node.getNodeSize()
      if not onBranch:
        # Back to the main branch
        xpos = mainBranchX
      if isinstance(node, _nuke.DotNode):
        # Start of new branch
        onBranch = True

        # We've hit a dot, we need to line all future dots up with this one
        reachedFirstBranch = True
        ypos = dotY

        # Set x position for new branch
        xpos = lastBranchX + 100
        lastBranchX = xpos

        # Correct for varying node sizes between the dot and the node at which we branch
        xoffset = (branchNodeW / 2)
        yoffset = (branchNodeH / 2) - (nodeH  / 2)
        xpos += xoffset
        ypos += yoffset

        # position the node
        xpos, ypos = self.layoutNode(node, xpos, ypos, LayoutBase.kAlignCenter, rect)
        
        # Undo the x correction 
        xpos -= xoffset

      elif isinstance(node, _nuke.WriteNode):
        xpos, ypos = self.layoutWriteNodes(node, xpos, ypos, alignment, rect)
        
        if not onBranch:
          mainBranchY = ypos

        # End of branch
        onBranch = False
        ypos = mainBranchY

      else:
        if not reachedFirstBranch:
          # Keep track our current y and node size until we branch for the first time
          dotY = ypos
          branchNodeW = nodeW
          branchNodeH = nodeH

        # Position the node on the current branch
        xpos, ypos = self.layoutNode(node, xpos, ypos, alignment, rect)

        if not onBranch:
          mainBranchY = ypos


    xpos = mainBranchX
    ypos = mainBranchY

    return rect


  # FIXME I'm not sure why but nodes in the writeNodes aren't explicitly
  # added to the Script object and hence aren't in the layoutContent. Due to
  # this we have to iterate through them here to make sure everything gets laid out.
  def layoutWriteNodes(self, writeNode, xpos, ypos, alignment, rect):
    writeNodes = writeNode.getNodes()
    writeNodes.append(writeNode)
    for n in writeNodes:
      xpos, ypos = self.layoutNode(n, xpos, ypos, alignment, rect)

    return xpos, ypos



class MergeLayout(LayoutBase):
  """ Layout for the merge and associated nodes. """

  def __init__(self, script, layoutContext):
    super(MergeLayout, self).__init__(script, layoutContext)

    self.leftMargin = 0
    self.rightMargin = 0
    self.topMargin = 20
    self.bottomMargin = 20
    self.shouldCreateBackdrop = False

  def layoutNodes(self, nodes, xpos, ypos, alignment):
    rect = QRect(xpos, ypos, 1, 1)

    firstNode = True

    for node in nodes:
      inputX, inputY = node.inputNodes()[1].getPosition()

      if inputX is None:
        inputX = xpos
      # Shift the rect to cover the position we will put the node at.
      if firstNode:
        rect = QRect(inputX, ypos, 0, 0)
        firstNode = False
      else:
        rect.setLeft(min(rect.left(), inputX))

      xpos, ypos = self.layoutNode(node, inputX, ypos, alignment, rect)

      if isinstance(node, _nuke.MergeNode):
        node.layoutDotInputs()

    return rect

  def getMainInputTrack(self):
    return self.layoutContext.getData("track")

  def getInputA(self):
    return self.layoutContext.getData("inputA")

  def subTrackItemsOnly(self):
    """ Merge layouts should act like layouts that only contain sub-track items, with layout vertically
        below the output track. """
    return True

  def getAlignHint(self):
    """ Get x and y positions to align to.  Aligns to the actual merge node and not any dot nodes which
    happen to be in the layout."""
    nodes = self.layoutContext.getNodes()
    for node in reversed(nodes):
      if isinstance(node, _nuke.MergeNode):
        nodeX, nodeY = node.getPosition()
        nodeW, nodeH = node.getNodeSize()
        return nodeX + (nodeW/2), nodeY + (nodeH/2)

    if self.rect is None:
      return 0, 0

    center = self.rect.center()
    return center.x(), center.y()



class EffectsTrackLayout(TrackLayout):
  """ Layout for the effects track and associated nodes. """

  def __init__(self, script, layoutContext):
    super(EffectsTrackLayout, self).__init__(script, layoutContext)

    self.leftMargin = 120
    self.rightMargin = 120

    self.shouldCreateBackdrop = True

  def layoutNodes(self, nodes, xpos, ypos, alignment):
    rect = QRect(xpos, ypos, 0, 0)

    firstNode = True

    for node in nodes:
      inputX, inputY = node.inputNodes()[0].getPosition()

      if inputX is None:
        inputX = xpos
      # Shift the rect to cover the position we will put the node at.
      if firstNode:
        rect.setRect(inputX, ypos, 0, 0)
        firstNode = False
      else:
        rect.setLeft(min(rect.left(), inputX))

      xpos, ypos = self.layoutNode(node, inputX, ypos, alignment, rect)

    return rect

  def getVerticallayoutAlignHint(self):
    if self._mergeLayout:
      return self._mergeLayout.getAlignHint()
    return self.getAlignHint()

  def layoutVertical(self, xpos, ypos, zorder):
    return self.doLayout(xpos, ypos, zorder)

  def layoutHorizontal(self, xpos, ypos, zorder):
    # Nothing to layout
    return QRect(xpos,ypos,0,0)

  def subTrackItemsOnly(self):
    """ Merge layouts should act like layouts that only contain sub-track items, with layout vertically
        below the output track. """
    return True



# Map layout contexts to their associated layout class
_layoutsDict = {
                "sequence" : SequenceLayout,
                "view" : ViewLayout,
                "track" : TrackLayout,
                "clip" : ClipLayout,
                "write" : WriteLayout,
                "merge" : MergeLayout,
                "effectsTrack" : EffectsTrackLayout
               }

class MainLayout(LayoutBase):
  """ Main layout, which arranges the clip/sequence and the write nodes with a gap in between. """

  kWriteLayoutSpacing = 200

  def __init__(self, script, layoutContext):
    super(MainLayout, self).__init__(script, layoutContext)


  def doLayout(self, xpos, ypos, zorder):
    self.rect = QRect(xpos,ypos,1,1)

    alignNode = None

    lastLayout = None
    # Layout everything apart from the write layout
    for childLayout in self.childLayouts[:-1]:
      #if not isinstance(childLayout, EffectsTrackLayout):
      self.rect |= childLayout.doLayout(xpos, ypos, zorder)
      xpos = self.rect.right() + self.childLayoutSpacing
      lastLayout = childLayout

    # Place the write layout, which should be the last of the child layouts.
    writeLayout = self.childLayouts[-1]
    writeLayoutWidth = writeLayout.getLayoutWidth()

    # Align the write to the last layout from our childLayouts
    alignX = 0
    alignY = 0
    if lastLayout:
      alignX, alignY = lastLayout.getAlignHint()

    xpos = alignX - (writeLayoutWidth / 2)
    ypos = self.rect.bottom() + MainLayout.kWriteLayoutSpacing

    self.rect |= writeLayout.doLayout(xpos, ypos, zorder+1)
    return  self.rect


def scriptLayout(script):
  """ Layout a script. """

  layout = MainLayout(script, script.getMainLayoutContext())
  layout.doLayout(0, 0, 0)

