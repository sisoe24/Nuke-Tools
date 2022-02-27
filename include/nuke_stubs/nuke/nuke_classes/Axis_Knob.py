from numbers import Number
from typing import *

import nuke
from . import *

class Axis_Knob(Knob):
    """
    A knob which descibes a 3D affine transformation, by combining rotations around each principal axis, scaling, translation, skew and a pivot point.
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

    def translate(self,):
        """
        self.translate() -> XYZ_Knob

        Return translation knob.
        """
        return XYZ_Knob()

    def rotate(self,):
        """
        self.rotate() -> XYZ_Knob

        Return rotation knob.
        """
        return XYZ_Knob()

    def scale(self,):
        """
        self.scale() -> Scale_Knob

        Return scale knob.
        """
        return Scale_Knob()

    def uniformScale(self,):
        """
        self.uniformScale() -> Double_Knob

        Return uniform scale knob.
        """
        return Double_Knob()

    def pivot(self,):
        """
        self.pivot() -> XYZ_Knob

        Return pivot knob.
        """
        return XYZ_Knob()

    def skew(self,):
        """
        self.skew() -> XYZ_Knob

        Return skew knob.
        """
        return XYZ_Knob()

    def value(self,):
        """
        self.value() -> _nukemath.Matrix4
        Return the transform matrix formed by combining the input knob values for translate, rotate, scale, skew and pivot.
        """
        return Any