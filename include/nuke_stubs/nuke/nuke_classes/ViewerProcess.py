from numbers import Number
from typing import *

import nuke
from . import *

class ViewerProcess(object):
    """
    ViewerProcess
    """
    def __hash__(self, ):
        """
        Return hash(self).
        """
        return None

    def register(self, name:str, call, args, kwargs=None):
        """
        nuke.ViewerProcess.register(name, call, args, kwargs) -> None.
        Register a ViewerProcess. This is a class method.
        @param name: Menu name.
        @param call: Python callable. Must return a Node.
        @param args: Arguments to call.
        @param kwargs: Optional named arguments.
        @return: None.
        """
        return None

    def unregister(self, name:str):
        """
        nuke.ViewerProcess.unregister(name) -> None.
        Unregister a ViewerProcess. This is a class method.
        @param name: Menu name.
        @return: None.
        """
        return None

    def node(self, name:str=None, viewer:str=None):
        """
        nuke.ViewerProcess.node(name, viewer) -> Node.
        Returns a ViewerProcess node. Default is to return the current selected one. This is a class method.
        @param name: Optional ViewerProcess name.
        @param viewer: Optional viewer name.
        @return: Node.
        """
        return Node()

    def registeredNames(self,):
        """
        nuke.ViewerProcess.registeredNames() -> List.
        Returns a list containing the names of all currently regisered ViewerProcesses.
        @return: List.
        """
        return list()

    def storeSelectionBeforeReload(self,):
        """
        nuke.ViewerProcess.storeSelectionBeforeReload() -> None.
        When the user reloads an OCIO or Nuke config the viewer process selection is stored in the the viewer process objectFollowing the reload you can call nuke.ViewerProcess.restoreSelectionAfterReload() which will then restore the selection instead of the default.@return: None.
        """
        return None

    def restoreSelectionAfterReload(self,):
        """
        nuke.ViewerProcess.restoreSelectionAfterReload() -> None.
        Restores the viewer process selection after an OCIO or Nuke Config has been reloadedthis is normally called after nuke.ViewerProcess.storeSelectionBeforeReload()@return: None.
        """
        return None

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None