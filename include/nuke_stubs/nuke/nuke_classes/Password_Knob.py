from numbers import Number
from typing import *

import nuke
from . import *

class Password_Knob(Knob):
    """
    A knob which holds a password string value. Appears as a password entry field in a Node panel.
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

    def getText(self,):
        """
        self.getText() -> string

        Return text associated with knob.
        """
        return str()

    def value(self,):
        """
        self.value() -> str

        Get the value of this knob as a string.
        @return: String value.
        """
        return str()

    def setValue(self, val:Any, view='default'):
        """
        self.setValue(val, view='default') -> None

        Set value of knob.
        @param val: The new value.
        @param view: Optional parameter specifying which view to set the value for. If omitted, the value will be set for the default view.
        @return: None
        """
        return None