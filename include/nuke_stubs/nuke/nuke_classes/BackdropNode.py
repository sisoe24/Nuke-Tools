from numbers import Number
from typing import *

import nuke
from . import *

class BackdropNode(Node):
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

    def selectNodes(self,selectNodes):
        """
        self.selectNodes(selectNodes) -> None
        Select or deselect all nodes in backdrop node
        Example:
        backdrop = nuke.toNode("BackdropNode1")
        backdrop.selectNodes(True)

        @return: None.
        """
        return None

    def getNodes(self,):
        """
        self.getNodes() -> a list of nodes contained inside the backdrop
        Get the nodes contained inside a backdrop node
        Example:
        backdrop = nuke.toNode("BackdropNode1")
        nodesInBackdrop = backdrop.getNodes()

        @return: a list of nodes contained inside the backdrop.
        """
        return list()

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None