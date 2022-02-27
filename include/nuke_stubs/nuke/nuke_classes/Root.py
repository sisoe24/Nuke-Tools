from numbers import Number
from typing import *

import nuke
from . import *

class Root(Group):
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

    def clones(self,):
        """
        self.clones() -> Number of clones.
        @return: Number of clones.
        """
        return Number()

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

    def maximumInputs(self,):
        """
        self.maximumInputs() -> Maximum number of inputs this node can have.
        @return: Maximum number of inputs this node can have.
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

    def modified(self,):
        """
        self.modified() -> True if modified, False otherwise.
        Get or set the 'modified' flag in a script
        @return: True if modified, False otherwise.
        """
        return bool()

    def setModified(self, b:bool):
        """
        self.setModified(b) -> None.
        Set the 'modified' flag in a script.
        Setting the value will turn the indicator in the title bar on/off and will start or stop the autosave timeout.
        @param b: Boolean convertible object.
        @return: None.
        """
        return None

    def proxy(self,):
        """
        self.proxy() -> True if proxy is set, False otherwise.
        @return: True if proxy is set, False otherwise.
        """
        return bool()

    def setProxy(self, b:bool):
        """
        self.setProxy(b) -> None.
        Set proxy.
        @param b: Boolean convertible object.
        @return: None.
        """
        return None

    def firstFrame(self,):
        """
        self.firstFrame() -> Integer.
        First frame.
        @return: Integer.
        """
        return int()

    def lastFrame(self,):
        """
        self.lastFrame() -> Integer.
        Last frame.
        @return: Integer.
        """
        return int()

    def fps(self,):
        """
        self.fps() -> integer
        Return the FPS rounded to an int. This is deprecated. Please use real_fps().
        """
        return int()

    def realFps(self,):
        """
        self.realFps() -> float
        The global frames per second setting.
        """
        return float()

    def mergeFrameRange(self, a:Number, b:Number):
        """
        self.mergeFrameRange(a, b) -> None.
        Merge frame range.
        @param a: Low-end of interval range.
        @param b: High-end of interval range.
        @return: None.
        """
        return None

    def addView(self, name:str, color:list=None):
        """
        self.addView(name, color) -> None.
        Add view.
        @param name: String - name of view.
        @param color: Optional. String in the format #RGB, #RRGGBB, #RRRGGGBBB, #RRRRGGGGBBBB or a name from the list of colors defined in the list of SVG color keyword names.
        @return: None.
        """
        return None

    def deleteView(self, s:str):
        """
        self.deleteView(s) -> None.
        Delete view.
        @param s: Name of view.
        @return: None.
        """
        return None

    def setFrame(self, n:Number):
        """
        self.setFrame(n) -> None.
        Set frame.
        @param n: Frame number.
        @return: None.
        """
        return None

    def setView(self, s:str):
        """
        self.setView(s) -> None.
        Set view.
        @param s: Name of view.
        @return: None.
        """
        return None

    def layers(self,):
        """
        nuke.Root.layers() -> Layer list.
        Class method.
        @return: Layer list.
        """
        return list()

    def channels(self,):
        """
        nuke.Root.channels() -> Channel list.
        Class method.
        @return: Channel list.
        """
        return list()

    def getOCIOColorspaceFromViewTransform(self, display:str, view:str):
        """
        nuke.root.getOCIOColorspaceFromViewTransform(display, view) -> Colorspace name
        Gets the name of the colorspace to which the specified display and view names are mapped
        for the root node's current OCIO config.
        @param display: Display name.
        @param view: View name.
        @return: The corresponding colorspace name.
        """
        return str()

    def getOCIOColorspaceFamily(self, colorspace:str):
        """
        nuke.root.getOCIOColorspaceFamily(colorspace) -> Family of colorspace
        Gets the name of the family to which the specified colorspace belongs,
        for the root node's current OCIO config.
        @param colorspace: Colorspace name.
        @return: Family name, may be an empty string.
        """
        return Any

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None