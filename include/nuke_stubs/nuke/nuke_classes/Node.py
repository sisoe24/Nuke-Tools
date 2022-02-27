from numbers import Number
from typing import *

import nuke
from . import *

class Node(object):
    """

    """
    def __repr__(self, ):
        """
        Return repr(self).
        """
        return None

    def __str__(self, ):
        """
        Return str(self).
        """
        return None

    def __len__(self, ):
        """
        Return len(self).
        """
        return None

    def __getitem__(self, key, ):
        """
        Return self[key].
        """
        return None

    def __new__(self,*args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        return None

    def Class(self,):
        """
        self.Class() -> Class of node.
        @return: Class of node.
        """
        return str()

    def clones(self,):
        """
        self.clones() -> Number of clones.
        @return: Number of clones.
        """
        return Number()

    def isCloneable(self,):
        """
        self.isCloneable() -> If the node permits cloning.
        @return: True if the node allows cloning, False otherwise.
        """
        return Any

    def inputs(self,):
        """
        self.inputs() -> Gets the maximum number of connected inputs.
        @return: Number of the highest connected input + 1. If inputs 0, 1, and 3 are connected, this will return 4.
        """
        return Number()

    def input(self, i:Number):
        """
        self.input(i) -> The i'th input.
        @param i: Input number.
        @return: The i'th input.
        """
        return int()

    def setInput(self, i:Number, node:Node):
        """
        self.setInput(i, node) -> bool
        Connect input i to node if canSetInput() returns true.
        @param i: Input number.
        @param node: The node to connect to input i.
        @return: True if canSetInput() returns true, or if the input is already correct.
        """
        return bool()

    def numKnobs(self,):
        """
        self.numKnobs() -> The number of knobs.
        @return: The number of knobs.
        """
        return Number()

    def numKnobs(self,):
        """
        self.numKnobs() -> The number of knobs.
        @return: The number of knobs.
        """
        return Number()

    def knob(self, p:Union[str, int], follow_link=None):
        """
        self.knob(p[, follow_link]) -> The knob named p or the pth knob.
        @param p: A string or an integer.
        @param follow_link: Should it follow links to Link_Knob until resolution. Default is True.
        @return: The knob named p or the pth knob.
        """
        return Knob()

    def optionalInput(self,):
        """
        self.optionalInput() -> Number of first optional input.
        @return: Number of first optional input.
        """
        return Number()

    def minimumInputs(self,):
        """
        self.minimumInputs() -> Minimum number of inputs this node can have.
        @return: Minimum number of inputs this node can have.
        """
        return Number()

    def minimumInputs(self,):
        """
        self.minimumInputs() -> Minimum number of inputs this node can have.
        @return: Minimum number of inputs this node can have.
        """
        return Number()

    def maximumInputs(self,):
        """
        self.maximumInputs() -> Maximum number of inputs this node can have.
        @return: Maximum number of inputs this node can have.
        """
        return Number()

    def maximumInputs(self,):
        """
        self.maximumInputs() -> Maximum number of inputs this node can have.
        @return: Maximum number of inputs this node can have.
        """
        return Number()

    def metadata(self, key:str=None, time:Number=None, view=None):
        """
        self.metadata(key, time, view) -> value or dict
        Return the metadata item for key on this node at current output context, or at optional time and view.
        If key is not specified a dictionary containing all key/value pairs is returned.
        None is returned if key does not exist on this node.
        @param key: Optional name of the metadata key to retrieve.
        @param time: Optional time to evaluate at (default is taken from node's current output context).
        @param view: Optional view to evaluate at (default is taken from node's current output context).
        @return: The requested metadata value, a dictionary containing all keys if a key name is not provided, or None if the specified key is not matched.
        """
        return Union[value, dict]

    def maximumOutputs(self,):
        """
        self.maximumOutputs() -> Maximum number of outputs this node can have.
        @return: Maximum number of outputs this node can have.
        """
        return Number()

    def maximumOutputs(self,):
        """
        self.maximumOutputs() -> Maximum number of outputs this node can have.
        @return: Maximum number of outputs this node can have.
        """
        return Number()

    def connectInput(self, i:Number, node:Node):
        """
        self.connectInput(i, node) -> bool
        Connect the output of 'node' to the i'th input or the next available unconnected input. The requested input is tried first, but if it is already set then subsequent inputs are tried until an unconnected one is found, as when you drop a connection arrow onto a node in the GUI.
        @param i: Input number to try first.
        @param node: The node to connect to input i.
        @return: True if a connection is made, False otherwise.
        """
        return bool()

    def canSetInput(self, i:Number, node:Node):
        """
        self.canSetInput(i, node) -> bool
        Check whether the output of 'node' can be connected to input i. 
        @param i: Input number.
        @param node: The node to be connected to input i.
        @return: True if node can be connected, False otherwise.
        """
        return bool()

    def name(self,):
        """
        self.name() -> str
        @return: Name of node.
        """
        return str()

    def help(self,):
        """
        self.help() -> str
        @return: Help for the node.
        """
        return str()

    def shown(self,):
        """
        self.shown() -> true if the properties panel is open. This can be used to skip updates that are not visible to the user.
        @return: true if the properties panel is open. This can be used to skip updates that are not visible to the user.
        """
        return bool()

    def showControlPanel(self, forceFloat = False):
        """
        self.showControlPanel(forceFloat = false) -> None
        @param forceFloat: Optional python object. If it evaluates to True the control panel will always open as a floating panel. Default is False.
        @return: None
        """
        return None

    def hideControlPanel(self,):
        """
        self.hideControlPanel() -> None
        @return: None
        """
        return None

    def setTab(self, tabIndex:int):
        """
        self.setTab(tabIndex) -> None
        @param tabIndex: The tab to show (first is 0).
        @return: None
        """
        return None

    def setName(self, name:str, uncollide=True, updateExpressions=False):
        """
        self.setName(name, uncollide=True, updateExpressions=False) -> None
        Set name of the node and resolve name collisions if optional named argument 'uncollide' is True.
        @param name: A string.
        @param uncollide: Optional boolean to resolve name collisions. Defaults to True.
        @param updateExpressions: Optional boolean to update expressions in other nodes to point at the new name. Defaults to False.
        @return: None
        """
        return None

    def fullName(self,):
        """
        self.fullName() -> str
        Get the name of this node and any groups enclosing it in 'group.group.name' form.
        @return: The fully-qualified name of this node, as a string.
        """
        return str()

    def xpos(self,):
        """
        self.xpos() -> X position of node in node graph.
        @return: X position of node in node graph.
        """
        return Number()

    def setXYpos(self, x:Number, y:Number):
        """
        self.setXYpos(x, y) -> None.
        Set the (x, y) position of node in node graph.
        @param x: The x position of node in node graph.
        @param y: The y position of node in node graph.
        @return: None.
        """
        return None

    def setXpos(self, x:Number):
        """
        self.setXpos(x) -> None.
        Set the x position of node in node graph.
        @param x: The x position of node in node graph.
        @return: None.
        """
        return None

    def setYpos(self, y:Number):
        """
        self.setYpos(y) -> None.
        Set the y position of node in node graph.
        @param y: The y position of node in node graph.
        @return: None.
        """
        return None

    def ypos(self,):
        """
        self.ypos() -> Y position of node in node graph.
        @return: Y position of node in node graph.
        """
        return Number()

    def setCustomIcon(self, image:str, scale:Number=None, offsetX=None, offsetY=None):
        """
        self.setCustomIcon(image, scale, offsetX, offsetY) -> bool.
        Set a custom icon for the node.
        @param image: filepath to image to be used as an icon.
        @param scale: Optional. scale factor for the icon.
        @param offsetX: Optional. offset the icon in the x axis from the top left corner of the node.
        @param offsetY: Optional. offset the icon in the y axis from the top left corner of the node.
        @return: True if icon has been set, else false.
        """
        return bool()

    def clearCustomIcon(self,):
        """
        self.clearCustomIcon() -> None.
        Clear the custom icon set for the node.
        @return: None.
        """
        return None

    def redraw(self,):
        """
        self.redraw() -> None.
        Force a redraw of the node.
        @return: None.
        """
        return None

    def addKnob(self, k:Knob):
        """
        self.addKnob(k) -> None.
        Add knob k to this node or panel.
        @param k: Knob.
        @return: None.
        """
        return None

    def removeKnob(self, k:Knob):
        """
        self.removeKnob(k) -> None.
        Remove knob k from this node or panel. Throws a ValueError exception if k is not found on the node.
        @param k: Knob.
        @return: None.
        """
        return None

    def showInfo(self, s:str):
        """
        self.showInfo(s) -> None.
        Creates a dialog box showing the result of script s.
        @param s: A string.
        @return: None.
        """
        return None

    def readKnobs(self, s:str):
        """
        self.readKnobs(s) -> None.
        Read the knobs from a string (TCL syntax).
        @param s: A string.
        @return: None.
        """
        return None

    def writeKnobs(self, i:Any):
        """
        self.writeKnobs(i) -> String in .nk form.
        Return a tcl list. If TO_SCRIPT | TO_VALUE is not on, this is a simple list
        of knob names. If it is on, it is an alternating list of knob names
        and the output of to_script().

        Flags can be any of these or'd together:
        - nuke.TO_SCRIPT produces to_script(0) values
        - nuke.TO_VALUE produces to_script(context) values
        - nuke.WRITE_NON_DEFAULT_ONLY skips knobs with not_default() false
        - nuke.WRITE_USER_KNOB_DEFS writes addUserKnob commands for user knobs
        - nuke.WRITE_ALL writes normally invisible knobs like name, xpos, ypos

        @param i: The set of flags or'd together. Default is TO_SCRIPT | TO_VALUE.
        @return: String in .nk form.
        """
        return str()

    def knobs(self,):
        """
        self.knobs() -> dict

        Get a dictionary of (name, knob) pairs for all knobs in this node.

        For example:

           >>> b = nuke.nodes.Blur()
           >>> b.knobs()

        @return: Dictionary of all knobs.

        Note that this doesn't follow the links for Link_Knobs
        """
        return dict()

    def allKnobs(self,):
        """
        self.allKnobs() -> list

        Get a list of all knobs in this node, including nameless knobs.

        For example:

           >>> b = nuke.nodes.Blur()
           >>> b.allKnobs()

        @return: List of all knobs.

        Note that this doesn't follow the links for Link_Knobs
        """
        return list()

    def running(self,):
        """
        self.running() -> Node rendering when paralled threads are running or None.
        Class method.
        @return: Node rendering when paralled threads are running or None.
        """
        return Node()

    def proxy(self,):
        """
        self.proxy() -> bool
        @return: True if proxy is enabled, False otherwise.
        """
        return bool()

    def sample(self, c:str, x:Number, y:Number, dx:Number=None, dy:Number=None):
        """
        self.sample(c, x, y, dx, dy) -> Floating point value.
        Return pixel values from an image.
        This requires the image to be calculated, so performance may be very bad if this is placed into an expression in
        a control panel. Produces a cubic filtered result. Any sizes less than 1, including 0, produce the same filtered result,
        this is correct based on sampling theory. Note that integers are at the corners of pixels, to center on a pixel add .5 to both coordinates.
        If the optional dx,dy are not given then the exact value of the square pixel that x,y lands in is returned. This is also called 'impulse filtering'.
        @param c: Channel name.
        @param x: Centre of the area to sample (X coordinate).
        @param y: Centre of the area to sample (Y coordinate).
        @param dx: Optional size of the area to sample (X coordinate).
        @param dy: Optional size of the area to sample (Y coordinate).
        @param frame: Optional frame to sample the node at.
        @return: Floating point value.
        """
        return float()

    def deepSample(self, c:str, x:Number, y:Number, n:int):
        """
        self.deepSample(c, x, y, n) -> Floating point value.
        Return pixel values from a deep image.
        This requires the image to be calculated, so performance may be very bad if this is placed into an expression in
        a control panel.
        @param c: Channel name.
        @param x: Position to sample (X coordinate).
        @param y: Position to sample (Y coordinate).
        @param n: Sample index (between 0 and the number returned by deepSampleCount() for this pixel, or -1 for the frontmost).
        @return: Floating point value.
        """
        return float()

    def deepSampleCount(self, x:Number, y:Number):
        """
        self.deepSampleCount(x, y) -> Integer value.
        Return number of samples for a pixel on a deep image.
        This requires the image to be calculated, so performance may be very bad if this is placed into an expression in
        a control panel.
        @param x: Position to sample (X coordinate).
        @param y: Position to sample (Y coordinate).
        @return: Integer value.
        """
        return int()

    def autoplace(self,):
        """
        self.autoplace() -> None.
        Automatically place nodes, so they do not overlap.
        @return: None.
        """
        return None

    def channels(self,):
        """
        self.channels() -> String list.
        List channels output by this node.
        @return: String list.
        """
        return list()

    def firstFrame(self,):
        """
        self.firstFrame() -> int.
        First frame in frame range for this node.
        @return: int.
        """
        return int()

    def lastFrame(self,):
        """
        self.lastFrame() -> int.
        Last frame in frame range for this node.
        @return: int.
        """
        return int()

    def error(self,):
        """
        error() -> bool
        True if the node or any in its input tree have an error, or False otherwise.

        Error state of the node and its input tree.  Deprecated; use hasError or treeHasError instead.
        Note that this will always return false for viewers, which cannot generate their input trees.  Instead, choose an input of the viewer (e.g. the active one), and call treeHasError() on that.
        """
        return bool()

    def treeHasError(self,):
        """
        treeHasError() -> bool
        True if the node or any in its input tree have an error, or False otherwise.

        Error state of the node and its input tree.
        Note that this will always return false for viewers, which cannot generate their input trees.  Instead, choose an input of the viewer (e.g. the active one), and call treeHasError() on that.
        """
        return bool()

    def hasError(self,):
        """
        hasError() -> bool
        True if the node itself has an error, regardless of the state of the ops in its input tree, or False otherwise.

        Error state of the node itself, regardless of the state of the ops in its input tree.
        Note that an error on a node may not appear if there is an error somewhere in its input tree, because it may not be possible to validate the node itself correctly in that case.
        """
        return bool()

    def frameRange(self,):
        """
        self.frameRange() -> FrameRange.
        Frame range for this node.
        @return: FrameRange.
        """
        return FrameRange()

    def upstreamFrameRange(self, i:Number):
        """
        self.upstreamFrameRange(i) -> FrameRange
        Frame range for the i'th input of this node.
        @param i: Input number.
        @return: FrameRange. Returns None when querying an invalid input.
        """
        return FrameRange()

    def format(self,):
        """
        self.format() -> Format.
        Format of the node.
        @return: Format.
        """
        return Format()

    def width(self,):
        """
        self.width() -> int.
        Width of the node.
        @return: int.
        """
        return int()

    def height(self,):
        """
        self.height() -> int.
        Height of the node.
        @return: int.
        """
        return int()

    def pixelAspect(self,):
        """
        self.pixelAspect() -> int.
        Pixel Aspect ratio of the node.
        @return: float.
        """
        return int()

    def screenWidth(self,):
        """
        self.screenWidth() -> int.
        Width of the node when displayed on screen in the DAG, at 1:1 zoom, in pixels.
        @return: int.
        """
        return int()

    def screenHeight(self,):
        """
        self.screenHeight() -> int.
        Height of the node when displayed on screen in the DAG, at 1:1 zoom, in pixels.
        @return: int.
        """
        return int()

    def bbox(self,):
        """
        self.bbox() -> List of x, y, w, h.
        Bounding box of the node.
        @return: List of x, y, w, h.
        """
        return list()

    def dependencies(self, what=None):
        """
        self.dependencies(what) -> List of nodes.

        List all nodes referred to by this node. 'what' is an optional integer (see below).
        You can use the following constants or'ed together to select what types of dependencies are looked for:
                 nuke.EXPRESSIONS = expressions
                 nuke.LINKINPUTS = link knobs
                 nuke.INPUTS = visible input pipes
                 nuke.HIDDEN_INPUTS = hidden input pipes.
        The default is to look for all types of connections.

        Example:
        nuke.toNode('Blur1').dependencies( nuke.INPUTS | nuke.EXPRESSIONS )
        @param what: Or'ed constant of nuke.EXPRESSIONS, nuke.INPUTS and nuke.HIDDEN_INPUTS to select the types of dependencies. The default is to look for all types of connections.
        @return: List of nodes.
        """
        return [Node]

    def dependent(self, what=None, forceEvaluate:bool=None):
        """
        self.dependent(what, forceEvaluate) -> List of nodes.

        List all nodes that read information from this node.  'what' is an optional integer:
                 You can use any combination of the following constants or'ed together to select what types of dependent nodes to look for:
                         nuke.EXPRESSIONS = expressions
                         nuke.LINKINPUTS = link knobs
                         nuke.INPUTS = visible input pipes
                         nuke.HIDDEN_INPUTS = hidden input pipes.
        The default is to look for all types of connections.

        forceEvaluate is an optional boolean defaulting to True. When this parameter is true, it forces a re-evaluation of the entire tree. 
        This can be expensive, but otherwise could give incorrect results if nodes are expression-linked. 

        Example:
        nuke.toNode('Blur1').dependent( nuke.INPUTS | nuke.EXPRESSIONS )
        @param what: Or'ed constant of nuke.EXPRESSIONS, nuke.INPUTS and nuke.HIDDEN_INPUTS to select the types of dependent nodes. The default is to look for all types of connections.
        @param forceEvaluate: Specifies whether a full tree evaluation will take place. Defaults to True.
        @return: List of nodes.
        """
        return [Node]

    def fileDependencies(self, start:Number, end:Number):
        """
        self.fileDependencies(start, end) -> List of nodes and filenames.

        @param start: first frame
        @param end: last frame
        Returns the list of input file dependencies for this node and all nodes upstream from this node for the given frame range.
        The file dependencies are calcuated by searching for Read ops or ops with a File knob.
        All views are considered and current proxy mode is used to decide on whether full format or proxy files are returned.
        Note that Write nodes files are also included but precomps, gizmos and external plugins are not.
        Any time shifting operation such as frameholds, timeblurs, motionblur etc are taken into consideration.
        @return The return list is a list of nodes and files they require.
        Eg.  [Read1, ['file1.dpx, file2.dpx'] ], [Read2, ['file3.dpx', 'file4.dpx'] ] ]
        """
        return list()

    def setSelected(self, selected:bool):
        """
        self.setSelected(selected) -> None.
        Set the selection state of the node.  This is the same as changing the 'selected' knob.
        @param selected: New selection state - True or False.
        @return: None.
        """
        return None

    def isSelected(self,):
        """
        self.isSelected() -> bool

        Returns the current selection state of the node.  This is the same as checking the 'selected' knob.
        @return: True if selected, or False if not.
        """
        return bool()

    def selectOnly(self,):
        """
        self.selectOnly() -> None.
        Set this node to be the only selection, as if it had been clicked in the DAG.
        @return: None.
        """
        return None

    def __reduce_ex__(self,*args, **kwargs):
        """
        Helper for pickle.
        """
        return None

    def opHashes(self,):
        """
        self.opHashes() -> list of int

        Returns a list of hash values, one for each op in this node.
        """
        return list()

    def linkableKnobs(self, knobType:list):
        """
        self.linkableKnobs(knobType) -> List

        Returns a list of any knobs that may be linked to from the node as well as some meta information about the knob. This may include whether the knob is enabled and whether it should be used for absolute or relative values. Not all of these variables may make sense for all knobs..
        @param knobType A KnobType describing the type of knobs you want.@return: A list of LinkableKnobInfo that may be empty .
        """
        return list()

    def forceValidate(self,):
        """
        self.forceValidate() -> None

        Force the node to validate itself, updating its hash.
        """
        return None

    def resetKnobsToDefault(self,):
        """
        self.resetKnobsToDefault() -> None

        Reset all the knobs to their default values.
        """
        return None

    def performanceInfo(self, category ):
        """
        self.performanceInfo( category ) -> Returns performance information for this node. Performance timing must be enabled.
        @category: performance category ( optional ).A performance category, must be either nuke.PROFILE_STORE, nuke.PROFILE_VALIDATE, nuke.PROFILE_REQUEST or nuke.PROFILE_ENGINE The default is nuke.PROFILE_ENGINE which gives the performance info of the render engine.
        @return: A dictionary containing the cumulative performance info for this category, where:
        callCount = the number of calls made
        timeTakenCPU =  the CPU time spent in microseconds
        timeTakenWall = the actual time ( wall time ) spent in microseconds
        """
        return Number()

    def isLocalized(self,):
        """
        self.isLocalized() -> returns True/False whether the node is completely localized.
        @return: bool
        """
        return bool()

    def forceUpdateLocalization(self,):
        """
        self.forceUpdateLocalization() -> Force Updates the localized files for this node.
        @return: None
        """
        return str()

    def localizationProgress(self,):
        """
        self.localizationProgress() -> Checks and reports on progress of localization of the current node.
        @return: float, between 0.0 (not localized) and 1.0 (localized)
        """
        return Any

    def isLocalizationOutdated(self,):
        """
        self.isLocalizationOutdated() -> Returns if there are changes detected in the source file.
        @return: true if the Localization source file has changed
        """
        return str()

    def rootNode(self,):
        """
        self.rootNode() -> Returns this node's root node. This may differ from nuke.root() for example if the read node was created importing footage to the timeline.
        """
        return Number()

    def parent(self,):
        """
        self.parent() -> Return the parent group node for this node.
        """
        return Any

    def lock(self,):
        """
        self.lock() -> Sets the node to a locked state where knobs cannot be edited.
        """
        return Any

    def unlock(self,):
        """
        self.unlock() -> Unlocks the node and makes knobs editable.
        """
        return Any

    def locked(self,):
        """
        self.locked() -> Returns True if the node is locked, False otherwise.
        """
        return bool()

    def addCallback(self,string, Callable):
        """
        self.addCallback(string, Callable) -> Add a callback to a specific event
        Specific callback type can be find in the documentation of the related type or function.
  
        """
        return Any

    def removeCallback(self,string):
        """
        self.removeCallback(string) -> Remove a callback to a specific event identified as a string.
        """
        return str()

    def clearCallbacks(self,):
        """
        self.clearCallbacks() -> Remove all callbacks on the node.
        """
        return Any

    def executeCallback(self,string):
        """
        self.executeCallback(string) -> Executes the callback, if exists related to the specified event.
        """
        return Any

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None