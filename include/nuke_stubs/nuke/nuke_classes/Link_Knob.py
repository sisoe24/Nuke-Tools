from numbers import Number
from typing import *

import nuke
from . import *

class Link_Knob(Knob):
    """
    Link_Knob
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

    def value(self,):
        """
        value() -> string

        Return value of knob.
        """
        return str()

    def setValue(self,):
        """
        setValue() -> None

        Set value of knob.
        """
        return None

    def setLink(self,s):
        """
        setLink(s) -> None
        """
        return None

    def makeLink(self,s, t):
        """
        makeLink(s, t) -> None
        """
        return None

    def getLinkedKnob(self,):
        """
        getLinkedKnob() -> knob
        """
        return knob()

    def getLink(self,):
        """
        getLink() -> s
        """
        return Any

    def applyOverride(self,):
        """
        applyOverride() -> bool
        This function only affects link knobs that are placed on a LiveGroup node. It replaces the value of the linked knob in the live group with the value set in the LiveGroup node.
        """
        return bool()

    def revertOverride(self,):
        """
        revertOverride() -> bool
        This function only affects link knobs that are placed on a LiveGroup node. When called the LinkKnob will revert to the linked knob value and will follow it after reloads.
        """
        return bool()