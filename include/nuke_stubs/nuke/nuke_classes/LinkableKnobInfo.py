from numbers import Number
from typing import *

import nuke
from . import *

class LinkableKnobInfo(object):
    """
    A linkable knob description. Holds a reference to a knob that may be linked to, as well as an indication whether this knob should be used as part of an absolute or relative expression and whether it is enabled.
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

    def knob(self,):
        """
        self.knob() -> Knob
        Returns the knob that may be linked to.
        """
        return Knob()

    def absolute(self,):
        """
        self.absolute() -> Boolean
        Returns whether the values of this knob should be treated as absolute or relative. This may be useful for positions.
        """
        return bool()

    def enabled(self,):
        """
        self.enabled() -> Boolean
        Returns whether the knob is currently enabled or not.
        """
        return bool()

    def displayName(self,):
        """
        self.displayName() -> String
        Returns the custom display name that will appear in Link-to menus.
        """
        return str()

    def indices(self,):
        """
        self.indices() -> List
        Returns a list of the knob channels that should be used with this linkable knob.
        """
        return list()

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None