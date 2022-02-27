from numbers import Number
from typing import *

import nuke
from . import *

class SceneGraph_Knob(Unsigned_Knob):
    """
    Displays a list of items as a hierarchy.
    The hierarchy is specified using back or forward slashes within the item names
    to specify their level in the tree. Handles multiple selection of items within the tree.
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

    def getItems(self,):
        """
        self.getItems() -> tuple of strings (name, type) 

        Returns a tuple of string tuples (name, type).
        """
        return str()

    def setItems(self, *args, autoSelect=False):
        """
        self.setItems([(name1, type1), (name2, type2), ...], autoSelect=false) -> None

        Sets the list of items that can be selected on the knob.@param items: sequence of string tuples (name, type) .
        @param autoSelect: If True, all items are automatically set as imported and selected.
        @return: None.
        """
        return None

    def addItems(self, *args, autoSelect=False):
        """
        self.addItems([(name1, type1), (name2, type2), ...], autoSelect=false) -> None

        Adds to the existing list of items that can be selected on the knob.@param items: sequence of string tuples (name, type) .
        @param autoSelect: If True, all items are automatically set as selected.
        @return: None.
        """
        return None

    def removeItems(self,*args):
        """
        self.removeItems([name1, name2, ...]) -> None

        Removes a list of string names from the knob.
        """
        return None

    def getSelectedItems(self,):
        """
        self.getSelectedItems() -> list

        @return: list of strings containing all currently selected items in the knob.
        """
        return list()

    def setSelectedItems(self, *args):
        """
        self.setSelectedItems([name1, name2, ...]) -> None

        @param items: sequence of strings - names of the items in the list .
        @return: None.
        .
        """
        return None