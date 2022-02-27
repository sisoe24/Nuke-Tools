from numbers import Number
from typing import *

import nuke
from . import *

class Pulldown_Knob(Enumeration_Knob):
    """
    Pulldown_Knob
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

    def numValues(self,):
        """
        numValues() -> int

        Return number of values.
        """
        return int()

    def itemName(self,n):
        """
        itemName(n) -> string

        Return name of item n. The argument n is an integer and in the range of 0 and numValues.
        """
        return str()

    def commands(self,n):
        """
        commands(n) -> string

        Return command n. The argument n is an integer and in the range of 0 and numValues.
        """
        return str()

    def value(self,):
        """
        self.value() -> String.
        Current value.
        @return: String.
        Example:
        w = nuke.nodes.Write()
        k = w['file_type']
        k.value()
        """
        return str()

    def setValues(self, items:str):
        """
        self.setValues(items) -> None.
        (Re)initialise knob to the list of items.
        @param items: Dictionary of name/value pairs.
        @param sort: Optional parameter as to whether to sort the names.
        @return: None.
        Example:
        w = nuke.nodes.NoOp()
        k = nuke.Pulldown_Knob('kname', 'klabel')
        k.setValues({'label/command' : 'eval("3*2")'})
        w.addKnob(k)
        k = w['kname']
        """
        return None