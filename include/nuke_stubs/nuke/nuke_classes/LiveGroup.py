from numbers import Number
from typing import *

import nuke
from . import *

class LiveGroup(Precomp):
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

    def makeLocal(self,):
        """
        makeLocal() -> None
        Puts the LiveGroup into "local" state.
        WARNING: This function is deprecated. Use makeEditable() instead.
        """
        return None

    def isLocal(self,):
        """
        isLocal() -> bool
        Checks if the LiveGroup is local.WARNING: This function is deprecated. Use published() instead.
        """
        return bool()

    def makeEditable(self,):
        """
        makeEditable() -> None
        Puts the LiveGroup into "editable" state.
        """
        return None

    def published(self,):
        """
        published() -> bool
        Returns True if the LiveGroup is published.
        """
        return bool()

    def publishLiveGroup(self, file:str=None):
        """
        publishLiveGroup(file) -> bool
        Writes a LiveGroup to a file. 
        @param file: (optional) The path to which we want to publish this LiveGroup. 
        If None then write to the path currently defined by the file knob.
        If the file specified by this param already exists, Nuke will attempt to over write it without a warning.
        Otherwise a new file will be created.
        @return: bool. True if successful, else, False.
        """
        return bool()

    def applyOverride(self,):
        """
        applyOverride() -> bool
        This function only affects link knobs that are placed on a LiveGroup type node. It replaces the value of the linked knob in the live group with the value set in the LiveGroup node.
        """
        return bool()

    def revertOverride(self,):
        """
        revertOverride() -> bool
        This function only affects link knobs that are placed on a LiveGroup type node. When called the LinkKnob will revert to the linked knob value and will follow it after reloads.
        """
        return bool()

    def anyOverrides(self,):
        """
        anyOverrides() -> bool
        If any of the exposed link knobs are overridden it returns with True.
        """
        return bool()

    def modified(self,):
        """
        modified() -> bool
        Returns True if the anything within the livegroup has changed.
        """
        return bool()

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None