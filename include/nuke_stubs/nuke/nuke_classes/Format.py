from numbers import Number
from typing import *

import nuke
from . import *

class Format(object):
    """
    A format.
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

    def name(self,):
        """
        self.name() -> string

        Returns the user-visible name of the format.
        """
        return str()

    def setName(self,name):
        """
        self.setName(name) -> None

        Set name of this format. The name parameter is the new name for the format.
        """
        return None

    def width(self,):
        """
        self.width() -> int

        Return the width of image file in pixels.
        """
        return int()

    def setWidth(self,newWidth):
        """
        self.setWidth(newWidth) -> None

        Set the width of image file in pixels.newWidth is the new width for the image; it should be a positive integer.
        """
        return None

    def height(self,):
        """
        self.height() -> int

        Return the height of image file in pixels.
        """
        return int()

    def setHeight(self,newHeight):
        """
        self.setHeight(newHeight) -> None

        Set the height of image file in pixels. newHeight is the new height for the image; it should be a positive integer.
        """
        return None

    def x(self,):
        """
        self.x() -> int

        Return the left edge of image file in pixels.
        """
        return int()

    def setX(self,newX):
        """
        self.setX(newX) -> None

        Set the left edge of image file in pixels. newX is the new left edge for the  image; it should be a positive integer.
        """
        return None

    def y(self,):
        """
        self.y() -> int

        Return the bottom edge of image file in pixels.
        """
        return int()

    def setY(self,newY):
        """
        self.setY(newY) -> None

        Set the bottom edge of image file in pixels. newY is the new bottom edge for the image; it should be a positive integer.
        """
        return None

    def r(self,):
        """
        self.r() -> int

        Return the right edge of image file in pixels.
        """
        return int()

    def setR(self,newR):
        """
        self.setR(newR) -> None

        Set the right edge of image file in pixels. newR is the new right edge for the image; it should be a positive integer.
        """
        return None

    def t(self,):
        """
        self.t() -> int

        Return the top edge of image file in pixels.
        """
        return int()

    def setT(self,newT):
        """
        self.setT(newT) -> None

        Set the top edge of image file in pixels. newY is the new top edge for the image; it should be a positive integer.
        """
        return None

    def pixelAspect(self,):
        """
        self.pixelAspect() -> float

        Returns the pixel aspect ratio (pixel width divided by pixel height) for this format.
        """
        return float()

    def setPixelAspect(self,aspectRatio):
        """
        self.setPixelAspect(aspectRatio) -> None

        Set a new pixel aspect ratio for this format. The aspectRatio parameter is the new ratio, found by dividing the desired pixel width by the desired pixel height.
        """
        return None

    def add(self,name):
        """
        self.add(name) -> None

        Add this instance to a list of "named" formats. The name parameter is the name of the list to add the format to.
        """
        return None

    def fromUV(self, u:Number, v:Number):
        """
        self.fromUV(u, v) -> [x, y]

        Transform a UV coordinate in the range 0-1 into the format's XY range. Returns a list containing the x and y coordinates.

        @param u: The U coordinate.
        @param v: The V coordinate.
        @return: [x, y]
        """
        return Iterable()

    def toUV(self, x:Number, y:Number):
        """
        self.toUV(x, y) -> (u, v)

        Back-transform an XY coordinate in the format's space into UV space.

        @param x: The X coordinate.
        @param y: The Y coordinate.
        @return: [u, v].
        """
        return Iterable()

    def scaled(self, sx:Number, sy, tx, ty):
        """
        scaled(sx, sy, tx, ty) -> Format

        Scale and translate this format by sx, sy, tx and ty.

        @param sx: Scale factor in X.@param sy: Scale factor in Y.@param tx: Offset factor in X.@param ty: Offset factor in Y.@return: Format.
        """
        return Format()