from numbers import Number
from typing import *

import nuke
from . import *

class Disable_Knob(Boolean_Knob):
    """
    A knob which holds a boolean value representing the disabled state of a node. This appears in a Node panel as a check box.
    """
    def __hash__(self, ):
        """
        Return hash(self).
        """
        return None

    def __lt__(self, value, ):
        """
        Return self<value.
        """
        return None

    def __le__(self, value, ):
        """
        Return self<=value.
        """
        return None

    def __eq__(self, value, ):
        """
        Return self==value.
        """
        return None

    def __ne__(self, value, ):
        """
        Return self!=value.
        """
        return None

    def __gt__(self, value, ):
        """
        Return self>value.
        """
        return None

    def __ge__(self, value, ):
        """
        Return self>=value.
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
        self.value() -> bool
        Get the boolean value for this knob.
        @return: True or False.
        """
        return bool()

    def setValue(self, b:bool):
        """
        self.setValue(b) -> bool
        Set the boolean value of this knob.
        @param b: Boolean convertible object.
        @return: True if modified, False otherwise.
        """
        return bool()