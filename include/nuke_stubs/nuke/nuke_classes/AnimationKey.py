from numbers import Number
from typing import *

import nuke
from . import *

class AnimationKey(object):
    """
    A control point for an animation curve.
    @var x
    The horizontal position of the point
    @var y
    The vertical position of the point
    @var lslope
    The derivative to the left of the point. If interpolation does not have
    USER_SET_SLOPE then this may not be correct until after evaluate() has been
    called.
    @var rslope
    The derivative to the right of the point. If interpolation does not have
    USER_SET_SLOPE then this may not be correct until after evaluate() has been
    called.
    @var la
    The left 'bicubic' value. This represents the horizontal
    position of the left bezier handle end, where 1.0 means 1/3 of the
    distance to the previous point. If both handles for a span are 1.0
    then the horizontal interpolation is linear and thus the vertical
    interpolation a cubic function.  The legal values are 0 to
    3. Setting outside of this range will produce undefined results.
    @var ra
    The right 'bicubic' value, again the legal range is 0 to 3.
    @var interpolation
    Used to calculate all the slopes except for the left slope of the first key
    and the right slope of the last key.
    Legal values are:
    - USER_SET_SLOPE: If this bit is on, the slopes are fixed by
                      the user and interpolation and extrapolation are ignored.
    - CONSTANT: The value of the curve is equal to the y of the
                point to the left.
    - LINEAR: slopes point directly at the next key.
    - SMOOTH: same as CATMULL_ROM but the slopes are clamped so that the
              convex-hull property is preserved (meaning no part of the curve
              extends vertically outside the range of the keys on each side of
              it). This is the default.
    - CATMULL_ROM: the slope at key n is set to the slope between the control
                   points n-1 and n+1. This is used by lots of software.
    - cubic: the slope is calculated to the only cubic interpolation which makes
             the first and second derivatives continuous. This type of
             interpolation was very popular in older animation software.  A
             different cubic interpolation is figured out for each set of adjacent
             points with the CUBIC type.
    - for the smooth, CATMULL_ROM, and CUBIC interpolations, the first and last
      key have slopes calculated so that the second derivative is zero at them.
    @var extrapolation
    controls how to set the left slope of the first point and the right slope of
    the last point. Notice that this can be set differently on the first and last
    points, and is also remembered on all internal points so if end points are
    deleted old behavior is restored).
    - constant: the left slope of the first point, and the right slope of the last
                point, are set to zero.
    - linear: (and all other values): The left slope of the first point is set
              equal to it's right slope (calculated by the interpolation).
    the right slope of the last point is set equal to it's left slope.
    if there is only one point both slopes are set to zero.
    @var selected
    True if the point is selected in the curve editor.
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

    @property
    def x(self) -> Any:
        """
        The horizontal position of the point
        """
        return None

    @property
    def y(self) -> Any:
        """
        The vertical position of the point
        """
        return None

    @property
    def lslope(self) -> Any:
        """
        The derivative to the left of the point
        """
        return None

    @property
    def rslope(self) -> Any:
        """
        The derivative to the right of the point
        """
        return None

    @property
    def la(self) -> Any:
        """
        The left 'bicubic' value
        """
        return None

    @property
    def ra(self) -> Any:
        """
        The right 'bicubic' value
        """
        return None

    @property
    def interpolation(self) -> Any:
        """
        Used to calculate all the slopes except for the left slope of the first key and the right slope of the last key
        """
        return None

    @property
    def extrapolation(self) -> Any:
        """
        Controls how to set the left slope of the first point and the right slope of the last point
        """
        return None

    @property
    def selected(self) -> Any:
        """
        True if the point is selected in the curve editor
        """
        return None