from numbers import Number
from typing import *

import nuke
from . import *

class GeoSelect_Knob(Knob):
    """
    A knob which allows selection of parts of a 3D object.
    """
    def __getattribute__(self, name, ):
        """
        Return getattr(self, name).
        """
        return None

    def __setattr__(self, name, value, ):
        """
        Implement setattr(self, name, value).
        """
        return None

    def __delattr__(self, name, ):
        """
        Implement delattr(self, name).
        """
        return None

    def getGeometry(self,):
        """
        self.getGeometry() -> _geo.GeometryList
        Get the geometry which this knob can select from.
        """
        return list()

    def getSelection(self,):
        """
        self.getSelection() -> list of lists of floats
        Returns the selection for each vertex as a float. If you access the result as selection[obj][pt], then obj is the index of the object in the input geometry and pt is the index of the point in that object.
        """
        return list()

    def getSelectionWeights(self,):
        """
        self.getSelectionWeights() -> list of lists of floats
        Returns the selection weights for each vertex as a float. If you access the result as selection[obj][pt], then obj is the index of the object in the input geometry and pt is the index of the point in that object. LALA
        """
        return list()

    def getSelectedFaces(self,):
        """
        self.getSelectedFaces() -> list of lists of floats
        Returns the selection for each face as a float. If you access the result as selection[obj][fc], then obj is the index of the object in the input geometry and fc is the index of the face in that object.
        """
        return list()

    def getFaceWeights(self,):
        """
        self.getFaceWeights() -> list of lists of floats
        Returns the selection weight for each face as a float. If you access the result as selection[obj][fc], then obj is the index of the object in the input geometry and fc is the index of the face in that object.
        """
        return list()

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None