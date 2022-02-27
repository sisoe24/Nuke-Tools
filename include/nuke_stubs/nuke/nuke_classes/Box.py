from numbers import Number
from typing import *

import nuke
from . import *

class Box(object):
    """
    A 2-dimensional rectangle. Described by left, right, top and bottom coords (width and height are calculated as necessary).
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

    def x(self,):
        """
        self.x() -> int

        The left edge of the box.
        """
        return int()

    def setX(self,n):
        """
        self.setX(n) -> None

        Set the left edge. The parameter n is an integer.
        """
        return None

    def y(self,):
        """
        self.y() -> int

        Return the bottom edge.
        """
        return int()

    def setY(self,n):
        """
        self.setY(n) -> None

        Set the bottom edge. The parameter n is an integer.
        """
        return None

    def r(self,):
        """
        self.r() -> int

        Return the right edge of the box.
        """
        return int()

    def setR(self,n):
        """
        self.setR(n) -> None

        Set the right edge. The parameter n is an integer.
        """
        return None

    def t(self,):
        """
        self.t() -> int

        Return top edge.
        """
        return int()

    def setT(self,n):
        """
        self.setT(n) -> None

        Set top edge.
        """
        return None

    def w(self,):
        """
        self.w() -> int

        Return width.
        """
        return int()

    def setW(self,n):
        """
        self.setW(n) -> None

        Set width by moving right edge.
        """
        return None

    def h(self,):
        """
        self.h() -> int

        Return height.
        """
        return int()

    def setH(self,n):
        """
        self.setH(n) -> None

        Set height by moving top edge.
        """
        return None

    def centerX(self,):
        """
        self.centerX() -> float

        Return center in X.
        """
        return float()

    def centerY(self,):
        """
        self.centerY() -> float

        Return height in Y.
        """
        return float()

    def set(self,x, y, r, t):
        """
        self.set(x, y, r, t) -> None

        Set all values at once.
        """
        return None

    def isConstant(self,):
        """
        self.isConstant() -> True if box is 1x1 in both directions, False otherwise.
        """
        return bool()

    def clear(self,):
        """
        self.clear() -> None.

        Set to is_constant().
        """
        return None

    def move(self,dx, dy):
        """
        self.move(dx, dy) -> None.

        Move all the sides and thus the entire box by the given deltas.
        """
        return None

    def pad(self,dx, dy, dr, dt):
        """
        self.pad(dx, dy, dr, dt) -> None.

        Move all the sides and thus the entire box by the given deltas.
        """
        return None

    def clampX(self,x):
        """
        self.clampX(x) -> int.

        Return x restricted to pointing at a pixel in the box.
        """
        return int()

    def clampY(self,y):
        """
        self.clampY(y) -> int.

        Return y restricted to pointing at a pixel in the box.
        """
        return int()

    def merge(self,x, y, r, t):
        """
        self.merge(x, y, r, t) -> None.

        Merge with the given edges.
        """
        return None

    def intersect(self,x, y, r, t):
        """
        self.intersect(x, y, r, t) -> None.

        Intersect with the given edges.
        """
        return None