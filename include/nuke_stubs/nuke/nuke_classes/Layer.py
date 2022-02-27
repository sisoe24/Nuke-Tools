from numbers import Number
from typing import *

import nuke
from . import *

class Layer(object):
    """
    A layer is a set of channels.
    """
    def __hash__(self, ):
        """
        Return hash(self).
        """
        return None

    def __new__(self,*args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        return None

    def visible(self,):
        """
        self.visible() -> bool
        Check whether the layer is visible.

        @return: True if visible, False if not.
        """
        return bool()

    def name(self,):
        """
        self.name() -> str
        Get the layer name.

        @return: The layer name, as a string.
        """
        return str()

    def setName(self, newName:str):
        """
        self.setName(newName) -> None
        Set the name of this layer.

        @param newName: The new name for this layer.
        """
        return None

    def channels(self,):
        """
        self.channels() -> [string, ...]
        Get a list of the channels in this layer.

        @return: A list of strings, where each string is the name of a channel in this layer.
        """
        return str()

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None