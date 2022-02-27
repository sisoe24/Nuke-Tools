from numbers import Number
from typing import *

import nuke
from . import *

class Hash(object):
    """
    A hash value for any number of objects.

    The append() method is used to add objects to the hash; the value will be recomputed efficiently as each new object is added.
    """
    def __hash__(self, ):
        """
        Return hash(self).
        """
        return None

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

    def __lt__(self, value, ):
        """
        Return self<value.
        """
        return None

    def __le__(self, value, ):
        """
        Return self<=value.
        """
        return None

    def __eq__(self, value, ):
        """
        Return self==value.
        """
        return None

    def __ne__(self, value, ):
        """
        Return self!=value.
        """
        return None

    def __gt__(self, value, ):
        """
        Return self>value.
        """
        return None

    def __ge__(self, value, ):
        """
        Return self>=value.
        """
        return None

    def __new__(self,*args, **kwargs):
        """
        Create and return a new object.  See help(type) for accurate signature.
        """
        return None

    def getHash(self,*args, **kwargs):
        """
        Get the current value of the hash.
        """
        return None

    def setHash(self,*args, **kwargs):
        """
        Set the current value of the hash.
        """
        return None

    def reset(self,*args, **kwargs):
        """
        Reset the hash.
        """
        return None

    def append(self,*args, **kwargs):
        """
        Add another value to the hash.
        """
        return None

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None