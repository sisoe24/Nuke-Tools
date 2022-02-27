from numbers import Number
from typing import *

import nuke
from . import *

class Group(Node):
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

    def nodes(self,):
        """
        self.nodes() -> List of nodes
        List of nodes in group.
        @return: List of nodes
        """
        return list()

    def numNodes(self,):
        """
        self.numNodes() -> Number of nodes
        Number of nodes in group.
        @return: Number of nodes
        """
        return Number()

    def node(self, s:str):
        """
        self.node(s) -> Node with name s or None.
        Locate a node by name.
        @param s: A string.
        @return: Node with name s or None.
        """
        return str()

    def run(self, callable):
        """
        self.run(callable) -> Result of callable.
        Execute in the context of node. All names are evaluated relative to this object.
        @param callable: callable to execute.
        @return: Result of callable.
        """
        return Any

    def begin(self,):
        """
        self.begin() -> Group.
        All python code that follows will be executed in the context of node. All names are evaluated relative to this object. Must be paired with end.
        @return: Group.
        """
        return Group()

    def end(self,):
        """
        self.end() -> None.
        All python code that follows will no longer be executed in the context of node. Must be paired with begin.
        @return: None.
        """
        return None

    def output(self,):
        """
        self.output() -> Node or None.
        Return output node of group.
        @return: Node or None.
        """
        return Union[Node, None]

    def selectedNode(self,):
        """
        self.selectedNode() -> Node or None.
        Returns the node the user is most likely thinking about. This is the last node the user clicked on, if it is selected.  Otherwise it is an 'output' (one with no selected outputs) of the set of selected nodes. If no nodes are selected then None is returned.
        @return: Node or None.
        """
        return Union[Node, None]

    def selectedNodes(self,):
        """
        self.selectedNodes() -> Node or None.
        Selected nodes.
        @return: Node or None.
        """
        return Union[Node, None]

    def connectSelectedNodes(self,backward, inputA):
        """
        self.connectSelectedNodes(backward, inputA) -> None.
        Connect the selected nodes.
        @param backward.
        @param inputA.
        @return: None.
        """
        return None

    def splaySelectedNodes(self,backward, inputA):
        """
        self.splaySelectedNodes(backward, inputA) -> None.
        Splay the selected nodes.
        @param backward.
        @param inputA.
        @return: None.
        """
        return None

    def expand(self,):
        """
        self.expand() -> None.
        Moves all nodes from the group node into its parent group, maintaining node input
        and output connections, and deletes the group.
        Returns the nodes that were moved, which will also be selected.
        @return: None.
        """
        return None

    def __enter__(self,*args, **kwargs):
        """

        """
        return None

    def __exit__(self,*args, **kwargs):
        """

        """
        return None

    def __reduce_ex__(self,*args, **kwargs):
        """
        Helper for pickle.
        """
        return None

    def subgraphLocked(self,*args, **kwargs):
        """

        """
        return None

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None