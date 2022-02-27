from numbers import Number
from typing import *

import nuke
from . import *

class Knob(object):
    """
    A modifiable control that appears (unless hidden) in the panel for a node.
    This is a base class that specific knob types inherit from.

    Knobs can be animated, have expressions, be disabled or hidden and more.
    """
    def __hash__(self, ):
        """
        Return hash(self).
        """
        return None

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None

    def __new__(self,*args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        return None

    def Class(self,):
        """
        self.Class() -> Class name.
        @return: Class name.
        """
        return str()

    def node(self,):
        """
        self.node() -> nuke.Node
        Return the node that this knob belongs to. If the node has been cloned, we'll always return a reference to the original.
        @return: The node which owns this knob, or None if the knob has no owner yet.
        """
        return nuke.Node()

    def name(self,):
        """
        self.name() -> name.
        @return: name.
        """
        return str()

    def setName(self, s:str):
        """
        self.setName(s) -> None.
        @param s: New name.
        @return: None.
        """
        return None

    def error(self, message:str):
        """
        self.error(message) -> None.
        @param message: message to put the knob in error.
        @return: None.
        """
        return None

    def critical(self, message:str):
        """
        self.critical(message) -> None.
        @param message: message to put the knob in error, and do a popup.
        @return: None.
        """
        return None

    def warning(self, message:str):
        """
        self.warning(message) -> None.
        @param message: message to put a warning on the knob.
        @return: None.
        """
        return None

    def debug(self, message:str):
        """
        self.debug(message) -> None.
        @param message: message to put out to the error console, attached to the knob, if the verbosity level is set high enough.
        @return: None.
        """
        return None

    def label(self,):
        """
        self.label() -> label.
        @return: label.
        """
        return str()

    def setLabel(self, s:str):
        """
        self.setLabel(s) -> None.
        @param s: New label.
        @return: None.
        """
        return None

    def tooltip(self,):
        """
        self.tooltip() -> tooltip.
        @return: tooltip.
        """
        return str()

    def setTooltip(self, s:str):
        """
        self.setTooltip(s) -> None.
        @param s: New tooltip.
        @return: None.
        """
        return None

    def setFlag(self, f):
        """
        self.setFlag(f) -> None.
        Logical OR of the argument and existing knob flags.
        @param f: Flag.
        @return: None.
        """
        return None

    def getFlag(self, f):
        """
        self.getFlag(f) -> Bool.
        Returns whether the input flag is set.
        @param f: Flag.
        @return: True if set, False otherwise.
        """
        return bool()

    def clearFlag(self, f):
        """
        self.clearFlag(f) -> None.
        Clear flag.
        @param f: Flag.
        @return: None.
        """
        return None

    def setValue(self,val, chan):
        """
        self.setValue(val, chan) -> bool

        Sets the value 'val' at channel 'chan'.
        @return: True if successful, False if not.
        """
        return bool()

    def setValueAt(self,val, time, chan):
        """
        self.setValueAt(val, time, chan) -> bool

        Sets the value 'val' at channel 'chan' for time 'time'.
        @return: True if successful, False if not.
        """
        return bool()

    def getValue(self,*args, **kwargs):
        """
        Return value at the current frame for channel 'c'.
        """
        return None

    def value(self,*args, **kwargs):
        """
        Return value at the current frame for channel 'c'.
        """
        return None

    def getValueAt(self,*args, **kwargs):
        """
        Return value at time 't' for channel 'c'.
        """
        return None

    def getKeyList(self,*args, **kwargs):
        """
        Get all unique keys on the knob.  Returns list.
        """
        return None

    def removeKey(self,*args, **kwargs):
        """
        Remove key for channel 'c'. Return True if successful.
        """
        return None

    def removeKeyAt(self,*args, **kwargs):
        """
        Remove key at time 't' for channel 'c'. Return True if successful.
        """
        return None

    def isKey(self,*args, **kwargs):
        """
        Return True if there is a keyframe at the current frame for channel 'c'.
        """
        return None

    def isKeyAt(self,*args, **kwargs):
        """
        Return True if there is a keyframe at time 't' for channel 'c'.
        """
        return None

    def getNumKeys(self,*args, **kwargs):
        """
        Return number of keyframes for channel 'c'.
        """
        return None

    def getKeyIndex(self,*args, **kwargs):
        """
        Return keyframe index at time 't' for channel 'c'.
        """
        return None

    def getKeyTime(self,*args, **kwargs):
        """
        Return index of the keyframe at time 't' for channel 'c'.
        """
        return None

    def getDerivative(self,*args, **kwargs):
        """
        Return derivative at time 't' for channel 'c'.
        """
        return None

    def getNthDerivative(self,*args, **kwargs):
        """
        Return nth derivative at time 't' for channel 'c'.
        """
        return None

    def getIntegral(self,*args, **kwargs):
        """
        Return integral at the interval [t1, t2] for channel 'c'.
        """
        return None

    def setAnimated(self,*args, **kwargs):
        """
        Set channel 'c' to be animated.
        """
        return None

    def isAnimated(self,*args, **kwargs):
        """
        Return True if channel 'c' is animated.
        """
        return None

    def clearAnimated(self,*args, **kwargs):
        """
        Clear animation for channel 'c'. Return True if successful.
        """
        return None

    def hasExpression(self, index=-1):
        """
        self.hasExpression(index=-1) -> bool
        Return True if animation at index 'index' has an expression.
        @param index: Optional index parameter. Defaults to -1 if not specified. This can be specified as a keyword parameter if desired.
        @return: True if has expression, False otherwise.
        """
        return bool()

    def setExpression(self, expression:str, channel=-1, view=None):
        """
        self.setExpression(expression, channel=-1, view=None) -> bool
        Set the expression for a knob. You can optionally specify a channel to set the expression for.

        @param expression: The new expression for the knob. This should be a string.
        @param channel: Optional parameter, specifying the channel to set the expression for. This should be an integer.
        @param view: Optional view parameter. Without, this command will set the expression for the current view theinterface is displaying. Can be the name of the view or the index.
        @return: True if successful, False if not.
        """
        return bool()

    def toScript(self,quote, context=None):
        """
        toScript(quote, context=current) -> string.

        Return the value of the knob in script syntax.
        Pass True for quote to return results quoted in {}.
        Pass None for context to get results for all views and key times (as stored in a .nk file).
        """
        return str()

    def fromScript(self,*args, **kwargs):
        """
        Initialise from script.
        """
        return None

    def fullyQualifiedName(self, channel=-1):
        """
        self.fullyQualifiedName(channel=-1) -> string
        Returns the fully-qualified name of the knob within the node. This can be useful for expression linking.

        @param channel: Optional parameter, specifies the channel number of the sub-knob (for example, channels of  0 and 1 would refer to the x and y of a XY_Knob respectively), leave blank or set to -1 to get the  qualified name of the knob only.
        @return: The string of the qualified knob or sub-knob, which can be used directly in expression links.
        """
        return str()

    def setEnabled(self, enabled:bool):
        """
        self.setEnabled(enabled) -> None.

        Enable or disable the knob.
        @param enabled: True to enable the knob, False to disable it.
        """
        return None

    def enabled(self,):
        """
        self.enabled() -> Boolean.

        @return: True if the knob is enabled, False if it's disabled.
        """
        return bool()

    def setVisible(self, visible:bool):
        """
        self.setVisible(visible) -> None.

        Show or hide the knob.
        @param visible: True to show the knob, False to hide it.
        """
        return None

    def visible(self,):
        """
        self.visible() -> Boolean.

        @return: True if the knob is visible, False if it's hidden.
        """
        return bool()