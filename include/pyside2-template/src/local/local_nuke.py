class Node:
    def __init__(self, node):
        self.node = node

    def name(self):
        return self.node + '1'

    def Class(self):
        return self.node

    def setSelected(self, value):
        pass


def allNodes():
    random_nodes = ['Merge', 'Viewer', 'Grade',
                    'Shuffle', 'Roto', 'Write', 'Read']

    return [Node(n) for n in random_nodes]


def toNode(node):
    return Node(node)


def zoomToFitSelected():
    pass


def nodesSelected():
    pass
