"""
Types for representing parameter ranges in the export code.

TODO This file ought to be renamed.
"""

class FloatRange(object):
  """ Representation of a range for floating point params, with min, max,
  and optional default values.
  """
  def __init__(self, min, max, default = None):
    self._min = min
    self._max = max
    self._default = default
  
  def min ( self ):
    return self._min
  def setMin( self, min ):
    self._min = min
  
  def max ( self ):
    return self._max
  def setMax ( self, max ):
    return self._max
    
  def default ( self ):
    return self._default
  def range ( self ):
    return self._max - self._min
  
  def __contains__ ( self, other ):
    a, b = self, other
    if hasattr(b, "min") and hasattr(b, "max"):
      if b.min() >= a.min():            
        if b.max() <= a.max():
          return True
    return False

class IntRange(FloatRange):
  """ Representation of a range for integer params, with min, max,
  and optional default values.

  NOTE: This class behaves exactly the same as FloatRange, it's just a way
  of signifying that a parameter is expected to have integer values.
  """
  def __init__(self, min, max, default = None):
    FloatRange.__init__(self, min, max, default)


class Default(object):
  """ Class indicating a default value in a list.

  TODO This is a terrible class name, and the way it's used makes it
  very easy to pass instances to code that's expecting the contained
  value.  Should be refactored.
  """
  def __init__(self, value):
    self._value = value
    
  def __repr__(self):
    return str(self._value)
    
  def value(self):
    return self._value
    

class QuicktimeSettings(object):
  def __init__(self, value=None):
    self._value = value
    
  def __repr__(self):
    return str(self._value)

  def value(self):
    return self._value
  
class QuicktimeCodec(object):
  def __init__(self, value=None):
    self._value = value
    
  def __repr__(self):
    return str(self._value)

  def value(self):
    return self._value
    
    
class CustomList(object):
  def __init__(self, *args, **kargs):
    self._values = list(args)
    self._default = kargs["default"]
    
  def __repr__(self):
    return str(self._values)

  def values(self):
    return self._values
    
  def default(self):
    return self._default
    
