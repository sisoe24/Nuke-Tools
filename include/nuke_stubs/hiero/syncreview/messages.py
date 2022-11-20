"""
Code for creating and serializing messages.
Message classes should be created with the defineMessageType() function, e.g.
messages.defineMessageType('MyMessage', ('someData', int))
"""

from hiero.core.util import (asBytes, asUnicode)
from PySide2.QtCore import (qCompress, qUncompress)
import json
from . log import logDebug

class Message(object):
  """ Class for messages used in the sync protocol. Concrete message types should
  be created with the defineMessageType() function.
  Each message has:
  - a sender, which should an id uniquely identifying the client machine
  - a target, which defaults to TARGET_BROADCAST indicating it should be routed to
    all clients, otherwise the server will try to send it to the specified client.
  - Optionally, a data payload
  """

  # Constant indicating a message is for general broadcast rather than a
  # specific recipient
  TARGET_BROADCAST = 'broadcast'

  def __init__(self, target):
    self.sender = ''
    self.target = target

  def serialize(self):
    """ Get the serialized representation of a message. This is in the form:
    [classname, sender, target, data...].
    """
    data = [asBytes(self.__class__.__name__), asBytes(self.sender), asBytes(self.target)]
    msgData = self._serializeMessageData()
    if msgData:
      data.extend(msgData)
    return data

  @classmethod
  def deserialize(cls, data):
    """ Factory method for constructing messages from their serialized representation
    """
    msg = cls()
    msg.sender = asUnicode(data[1])
    msg.target = asUnicode(data[2])
    if len(data) > 3:
      msgContent = data[3:]
      msg._deserializeMessageData(msgContent)
    return msg

  def __str__(self):
    data = self.serialize()
    name = data[0]
    data = data[1:]
    def _dataStr(d):
      return str(d) if len(d) < 100 else 'data(size={})'.format(len(d))
    return "{}({})".format(name,
                           ','.join(_dataStr(d) for d in data))


def defineMessageType(className, *fieldDefs):
  """ Define a new message class which will be added to the messages module.
  Fields can be defined with a name and specification of how they should be serialized.
  This can be just a type or conversion function, e.g. ('myField', int) where for
  serialization the data will just be converted to a string.
  Where control is needed over the serialization as well, you can specify a pair
  of functions, e.g. ('myField', (ValueToData, ValueFromData)). In this case they
  should return and accept a bytes object respectively
  """
  # Split the field definition tuples into a list of names and serialization functions
  # If the serializer was a single object, use str cast to serialize, then convert
  # to UTF-8 string. When unserializing, we need to convert from bytes to str,
  # then apply the conversion function
  fieldNames = []
  fieldSerializers = []
  for fieldName, fieldSerializer in fieldDefs:
    fieldNames.append(fieldName)

    if isinstance(fieldSerializer, tuple):
      fieldSerializers.append(fieldSerializer)
    else:
      toData = lambda d: asBytes(asUnicode(d))
      # Note capturing fieldSerializer as default to dummy arg
      fromData = lambda d, x=fieldSerializer: x(asUnicode(d))
      fieldSerializers.append((toData, fromData))

  # Define the init function. Sets the field values from the keyword arguments
  def __init__(self, target=Message.TARGET_BROADCAST, **fields):
    Message.__init__(self, target)
    for key, value in fields.items():
      i = fieldNames.index(key)
      setattr(self, key, value)

  # Serialize the message data to a list of string objects using the conversion
  # functions specified
  def _serializeMessageData(self):
    return [asBytes(serializers[0](getattr(self, name))) for name, serializers in zip(fieldNames, fieldSerializers)]

  # Deserialize the message data from a list of string objects using the conversion
  # functions specified
  def _deserializeMessageData(self, data):
    for name, serializers, value in zip(fieldNames, fieldSerializers, data):
      setattr(self, name, serializers[1](value))

  # Create the class and insert it into this module's namespace
  methods = { '__init__' : __init__,
              '_serializeMessageData' : _serializeMessageData,
              '_deserializeMessageData' : _deserializeMessageData }
  msgClass = type(className, (Message,), methods)
  globals()[className] = msgClass
  return msgClass


def deserializeMessage(data):
  """ Factory function for creating a message instance from its serialized
  representation.
  """
  # Look up the class by name in the module dictionary and create an instance
  typeName = asUnicode(data[0])
  msgType = globals()[typeName]
  return msgType.deserialize(data)


def RemoveDuplicateMessagesFilter(msgType, matchAttributes=None):
  """ Create filter which only keeps the latest of messages in a list matching
  msgType. If a list of attributes to match is also specified, earlier messages
  of the same type are discarded if they have the same values for those attributes
  as a later message
  """

  # Helper for comparing a set of attributes on messages
  def _compareAttrs(msgA, msgB, attrs):
    for attr in attrs:
      if getattr(msgA, attr) != getattr(msgB, attr):
        return False
    return True

  def _inner(msgList):
    filteredList = []
    lastMatchingMsgs = []
    # Reverse iterate to find the latest matching messages first
    for msg in reversed(msgList):
      discard = False
      if isinstance(msg, msgType):
        if not lastMatchingMsgs: # Found first matching message
          lastMatchingMsgs.append(msg)
        else:
          # Discard any duplicate messages. If attributes to match against were
          # given only discard if they match the ones we're keeping
          discard = True
          if matchAttributes:
            for matchMsg in lastMatchingMsgs:
              if not _compareAttrs(msg, matchMsg, matchAttributes):
                discard = False
                lastMatchingMsgs.append(msg)
      if not discard:
        filteredList.insert(0, msg)
    return filteredList
  return _inner


__messageFilters = []

def addMessageFilter(filter):
  """ Add a filter for incoming messages. This should be a callable which takes
  a list of messages and returns the filtered list.
  """
  global __messageFilters
  __messageFilters.append(filter)

def applyMessageFilters(msgList):
  """ Filter a set of incoming messages. This can be used to e.g. discard duplicate
  messages when only the most recent one is needed.
  Returns the filtered list.
  """
  count = len(msgList)
  if count <= 1:
    return msgList
  global __messageFilters
  filteredList = msgList
  for filter in __messageFilters:
    filteredList = filter(filteredList)
  if len(msgList) != len(filteredList):
    logDebug("applyMessageFilters original count: {} filtered count: {}".format(len(msgList), len(filteredList)))
  return filteredList



# Helpers for declaring a field whose data should be compressed.
# Note: compression converts the passed data to bytes. Decompression returns bytes
Compressed = ((lambda d : qCompress(asBytes(d)).data()),
              (lambda d : qUncompress(d).data()))

# Helpers for declaring a field whose data can be serialized to JSON
Json = ((lambda d: asBytes(json.dumps(d, separators=(',', ':')))),
        (lambda d: json.loads(d)))

# Handle a bool field, represented with '1' and '0'
Bool = ((lambda d: b'1' if d else b'0'),
        (lambda d: d == b'1'))

# Message type definitions
defineMessageType('Connect',
                    ('protocolVersion', str),
                    ('applicationVersion', str),
                    ('clientData', Json))
defineMessageType('ConnectResponse', ('result', int), ('responseText', str))

defineMessageType('Disconnect')
defineMessageType('Disconnected', ('disconnected', str))
defineMessageType('Ping')
defineMessageType('Pong')
defineMessageType('NumberOfPeers', ('content', int))
defineMessageType('Notification', ('message', str))
