from numbers import Number
from typing import *

import nuke
from . import *

class SceneView_Knob(Unsigned_Knob):
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

    def getImportedItems(self,):
        """
        self.getImportedItems() -> list

        Returns a list of strings containing all items imported into the knob.
        """
        return list()

    def setImportedItems(self, items:list):
        """
        self.setImportedItems(items) -> None

        Sets a list of strings containing all items imported into the knob. This will overwrite the current imported items list.@param items: List of imported items.
        @return: None.
        """
        return None

    def getAllItems(self,):
        """
        self.getAllItems() -> list

        Returns a list of strings containing all items that the knob can import.
        """
        return list()

    def setAllItems(self, items:list, autoSelect:bool):
        """
        self.setAllItems(items, autoSelect) -> None

        Sets a list of strings containing all items that the knob can import.
        After calling this function, only items from this list can be imported into the nosde.
        @param items: List of imported items.
        @param autoSelect: If True, all items are automatically set as imported and selected.
        @return: None.
        """
        return None

    def addItems(self,):
        """
        self.addItems() -> None

        Adds a list of string items to the knob. New items are automatically set as imported and selected.
        """
        return None

    def removeItems(self,):
        """
        self.removeItems() -> None

        Removes a list of string items from the knob.
        """
        return None

    def getSelectedItems(self,):
        """
        self.getSelectedItems() -> list

        Returns a list of strings containing all currently selected items in the knob.
        """
        return list()

    def setSelectedItems(self,):
        """
        self.setSelectedItems() -> None

        Takes a list of strings of items contained in the knob and sets them as selected.
        """
        return None

    def getHighlightedItem(self,):
        """
        self.getHighlightedItem() -> string

        Returns a string containing the item which is currently highlighted.
        """
        return str()