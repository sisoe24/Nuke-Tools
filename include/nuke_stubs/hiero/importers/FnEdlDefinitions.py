#! /usr/bin/python3

from .yeanpypa import *
from .FnEdlStructures import *

from types import *
import hiero.core
    
SPACE = Literal(' ')

TERMINATOR  =  (Literal('\r\n') | Literal('\r') | Literal('\n') | Literal('\x1a').hide() )

ACTUAL_SEPARATOR =  SPACE | \
                    Literal('\t') | \
                    Literal('\\') + TERMINATOR

# One or more actual separators
SEPARATOR = OneOrMore(ACTUAL_SEPARATOR)

UPPER_ALPHA = AnyOf('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

LOWER_ALPHA = AnyOf('abcdefghijklmnopqrstuvwxyz')
              
ALPHA       = alpha

NON_ZERO_DIGIT = AnyOf('123456789')

DIGIT     = digit

HEXADECIMAL_DIGIT = hexdigit

PRINTABLE_CHARACTER = (AnyOf('!"#%&()*+-/<=>?@[\\]^_\'{|}~:;,.$') | ALPHA | DIGIT) 

PRINTABLE_STRING      = (Word(PRINTABLE_CHARACTER))

HEXADECIMAL_NUMBER    = Optional(Literal('0x') | Literal('0X')).hide() + Word(HEXADECIMAL_DIGIT)

NUMBER                = Word(DIGIT)

SIGNED_NUMBER         = Combine(Literal('+') + NUMBER | Literal('-') + NUMBER | NUMBER)

INTEGER               = Combine(SIGNED_NUMBER).setAction(lambda x: int(x[0]))

REAL_NUMBER           = Combine((Optional(SIGNED_NUMBER) + Literal('.') + NUMBER) | SIGNED_NUMBER).setAction(lambda x: float(x[0]))

LEADING_RADIX_NUMBER  = (Combine(DIGIT + DIGIT) | Combine(DIGIT)).setAction(lambda x: int(x[0]))

RADIX_NUMBER          = Combine(DIGIT + DIGIT).setAction(lambda x: int(x[0]))

# Time Codes
TIME_CODE_SEPARATOR   = (Literal(':') | Literal(';') | Literal(',') | Literal('.'))

TIME_CODE_FIELD_SPECIFIER = LEADING_RADIX_NUMBER

SUB_FRAME_SPECIFIER   =  Literal('%').hide() + REAL_NUMBER

TIME_CODE_FIELD_SPECIFIER = \
      (LEADING_RADIX_NUMBER + TIME_CODE_SEPARATOR + RADIX_NUMBER + TIME_CODE_SEPARATOR + RADIX_NUMBER + TIME_CODE_SEPARATOR + RADIX_NUMBER) \
    | (LEADING_RADIX_NUMBER + TIME_CODE_SEPARATOR + RADIX_NUMBER + TIME_CODE_SEPARATOR + RADIX_NUMBER) \
    | (LEADING_RADIX_NUMBER + TIME_CODE_SEPARATOR + RADIX_NUMBER) \
    | (TIME_CODE_SEPARATOR + RADIX_NUMBER) 

TIME_CODE_SUB_FIELD_SPECIFIER = TIME_CODE_FIELD_SPECIFIER + SUB_FRAME_SPECIFIER

TIME_CODE = TIME_CODE_FIELD_SPECIFIER #| TIME_CODE_SUB_FIELD_SPECIFIER

# Source Element
EDIT_NUMBER_SUBFIELD  = NUMBER #DIGIT | DIGIT + ALPHA      #Note the limit to 6 digits.
EDIT_NUMBER           = EDIT_NUMBER_SUBFIELD

IDENTIFIER             = PRINTABLE_STRING

FILENAME              = Literal('"') + PRINTABLE_STRING + Literal('"')

EFFECT_PARAMETER_FIELD = REAL_NUMBER #| REAL_NUMBER + EFFECT_LIMIT_SUBFIELD

SINGLE_SOURCE_EFFECT  = Literal('C') | \
                       Literal('R')
					   
MULTIPLE_SOURCE_EFFECT = (Literal('K') | Literal('D')) + (INTEGER | PRINTABLE_CHARACTER)


EFFECT_FIELD          = (MULTIPLE_SOURCE_EFFECT) | (SINGLE_SOURCE_EFFECT)

AUDIO_TRACK_NUMBER    = INTEGER 	 

#The second track number must be greater than the first track number.
AUDIO_RANGE           = AUDIO_TRACK_NUMBER + Literal('-') + AUDIO_TRACK_NUMBER

MODE_AUDIO_SUBFIELD   = AUDIO_RANGE | AUDIO_TRACK_NUMBER 

MODE_FIELD            = (Literal('AA') + OneOrMore(MODE_AUDIO_SUBFIELD + Literal(',').hide() | MODE_AUDIO_SUBFIELD)) | \
                        (Literal('A') + OneOrMore(MODE_AUDIO_SUBFIELD + Literal(',').hide() | MODE_AUDIO_SUBFIELD)) | \
                        (Literal('B') + OneOrMore(MODE_AUDIO_SUBFIELD + Literal(',').hide() | MODE_AUDIO_SUBFIELD)) | \
                        Literal('V') | \
                        Literal('AA/V') | \
                        Literal('AA') | \
                        Literal('A') | \
                        Literal('B') | \
                        Literal('NONE')

SOURCE_ENTRY_FIELD    = TIME_CODE #| TIME_CODE + PLAYBACK_SUBFIELD

SOURCE_EXIT_FIELD     = TIME_CODE

SYNC_ENTRY_FIELD      = TIME_CODE

SYNC_EXIT_FIELD       = TIME_CODE

SOURCE_IDENTIFICATION_FIELD = IDENTIFIER
                #IDENTIFIER | IDENTIFIER + Literal('.') + MODE_AUDIO_SUBFIELD

# DLELD Elements
DLEDL_EDIT_FILENAME_ELEMENT     = (Literal('FILENAME') + Literal(':').hide() +  Word(NoneOf("\n\r")))
DLEDL_EDIT_RESOLUTION_ELEMENT   = (Literal('RESOLUTION') + Literal(':').hide() + PRINTABLE_STRING )
DLEDL_EDIT_FRAME_ELEMENT        = Literal('FRAME') + Literal(':').hide() + HEXADECIMAL_NUMBER

DLEDL_EDIT_ELEMENT    = Combine(Literal('EDIT:') + NUMBER).hide() + \
                         (DLEDL_EDIT_FILENAME_ELEMENT | \
                         DLEDL_EDIT_RESOLUTION_ELEMENT | \
                         DLEDL_EDIT_FRAME_ELEMENT)

DLEDL_PATH_ELEMENT    = Literal('PATH') + Literal(':').hide() + PRINTABLE_STRING

DLEDL_START_ELEMENT   = Combine(Literal('START') + Literal('TC') + Literal(':').hide()) + TIME_CODE


def NamedElementAction(x):
  y = flatten(x)
  return NamedElement(y[0], y[1])
  
def MultipleEffectFieldAction(x):
  y = flatten(x)
  return EffectField(y[0], y[1])
  
MULTIPLE_SOURCE_EFFECT.setAction(MultipleEffectFieldAction)
	
def SingleEffectFieldAction(x):
  return EffectField(x[0], 0)

SINGLE_SOURCE_EFFECT.setAction(SingleEffectFieldAction)


def SourceElementAction(x):
  x = flatten(x)
  result = []
  editdecision = EditDecision('---', x[0], x[1], x[2], x[3], x[4], x[5], x[6])
  result.append(editdecision)
  for element in x[8:]:
    if isinstance(element, NamedElement):
      editdecision.addElement(element)
    else:
      result.append(element)
    
  return result

def IndexedSourceElementAction(x):
  x = flatten(x)
  result = []
  editdecision = EditDecision(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7])
  result.append(editdecision)
  for element in x[8:]:
    if isinstance(element, NamedElement):
      editdecision.addElement(element)
    elif isinstance(element, RetimeElement):
      result.append(element)
    
  return result


def AudioRangeAction(x):
  y = list(range(int(x[0]), int(x[2])))
  return y

AUDIO_RANGE.setAction(AudioRangeAction)

def SourceModeFieldAction(x):
  x = flatten(x)
  mode = x[0]

  audio = False
  video = False
  audiochannels = x[1:]
  minaudiochannels = 0
  
  if mode == 'A':
    audio = True
    minaudiochannels = 1
  elif mode == 'AA':
    audio = True
    minaudiochannels = 2
  elif mode == 'V':
    video = True
  elif mode == 'AA/V':
    audio = True
    video = True
    minaudiochannels = 2
  elif mode == 'B':
    audio = True
    video = True
    minaudiochannels = 1
  elif mode == 'NONE':
    audio = False
    video = False

  
  for chan in range(1, minaudiochannels +1):
    if len(audiochannels) < minaudiochannels:
      audiochannels.append(chan)

  return ModeField(audio, video, audiochannels)

MODE_FIELD.setAction(SourceModeFieldAction)


DLEDL_ELEMENT = (Literal('DLEDL:').hide() + \
                (DLEDL_EDIT_ELEMENT | \
                DLEDL_PATH_ELEMENT | \
                DLEDL_START_ELEMENT))

def RetimeElementAction(x):
  if len(x) == 3:
    # The M2 command had no source entry value.
    return RetimeElement(x[1], x[2])
  return RetimeElement(x[1], x[2], x[3])

RETIME_DIRECTIVE        = Literal("M2") + SOURCE_IDENTIFICATION_FIELD + REAL_NUMBER + Optional(SOURCE_ENTRY_FIELD)

RETIME_DIRECTIVE.setAction(RetimeElementAction)


# This is the main EDL Element
INDEXED_SOURCE_ELEMENT =  ((EDIT_NUMBER + \
                  SOURCE_IDENTIFICATION_FIELD + \
                  MODE_FIELD + \
                  EFFECT_FIELD + \
                  SOURCE_ENTRY_FIELD + \
                  SOURCE_EXIT_FIELD + \
                  SYNC_ENTRY_FIELD + \
                  SYNC_EXIT_FIELD)).setAction(IndexedSourceElementAction)

SOURCE_ELEMENT =  ((SOURCE_IDENTIFICATION_FIELD + \
                  MODE_FIELD + \
                  EFFECT_FIELD + \
                  SOURCE_ENTRY_FIELD + \
                  SOURCE_EXIT_FIELD + \
                  SYNC_ENTRY_FIELD + \
                  SYNC_EXIT_FIELD)).setAction(SourceElementAction)

INFORMATIONAL_DIRECTIVE = Combine((Literal('*') | ALPHA) + Word(NoneOf("\n\r")))

SYSTEM_DIRECTIVE = ((Literal('TITLE') | Literal('FCM')) + Optional(Literal(':')).hide() + Word(NoneOf("\n\r"))).setAction(NamedElementAction)
                   
# Ommited AUTO_ASSEMBLE_DIRECTIVE | CONTROL_DIRECTIVE | MISCELLANEOUS_DIRECTIVE | MOTION_DIRECTIVE

FROMCLIP_ELEMENT = (Combine(Literal('FROM') + Literal('CLIP') + Literal('NAME') + Literal(':').hide()) +  Word(NoneOf("\n\r")))
TOCLIP_ELEMENT = (Combine(Literal('TO') + Literal('CLIP') + Literal('NAME') + Literal(':').hide()) +  Word(NoneOf("\n\r")))
KEYCLIP_ELEMENT = (Combine(Literal('KEY') + Literal('CLIP') + Literal('NAME') + Literal(':').hide()) +  Word(NoneOf("\n\r")))   
FCP_ELEMENT = (Literal('FINAL') + Literal('CUT') + Literal('PRO') + Word(NoneOf("\n\r")))

# This might be 'SOURCE FILE:' or 'SOURCE FILE PATH:'.
SOURCEFILE_ELEMENT = (Combine(Literal('SOURCE') + Literal('FILE') + Optional(Literal('PATH')).hide() + Literal(':').hide()) +  Word(NoneOf("\n\r")))

# Action to handle the optional 'additional' audio tracks 3 and/or 4. These are specified with NONE in the
# mode field (i.e., edit type) with AUD 3, AUD 4 or AUD 3 4 appearing on a subsequent line to the main source element listing.
# A regular NamedElement object is returned but with the value being a list of integers, [3], [4] or [3,4].
def Aud34Action(x):
  flattened = flatten(x)
  channels = [ int(channel) for channel in flattened[1].split() ]
  return NamedElement(flattened[0], channels)
  
AUD_ELEMENT = (Literal('AUD') + Word(NoneOf("\n\r")))

COMMENT_ELEMENT = (Optional(Literal('*')).hide() + ( \
                  (FROMCLIP_ELEMENT) | \
                  (TOCLIP_ELEMENT) | \
                  (KEYCLIP_ELEMENT) | \
                  (FCP_ELEMENT) | \
                  (SOURCEFILE_ELEMENT) ))

DLEDL_ELEMENT.setAction(NamedElementAction)
FROMCLIP_ELEMENT.setAction(NamedElementAction)
TOCLIP_ELEMENT.setAction(NamedElementAction)
KEYCLIP_ELEMENT.setAction(NamedElementAction)
SOURCEFILE_ELEMENT.setAction(NamedElementAction)
AUD_ELEMENT.setAction(Aud34Action)


# Format is user defined.
USER_ELEMENT = EDIT_NUMBER + Literal('?') + PRINTABLE_STRING

#
EDIT_SUB_ELEMENT =  OneOrMore((DLEDL_ELEMENT)| (USER_ELEMENT) | (COMMENT_ELEMENT) | (RETIME_DIRECTIVE) | (AUD_ELEMENT) | (INFORMATIONAL_DIRECTIVE))

INDEXED_EDIT_ELEMENT = ((INDEXED_SOURCE_ELEMENT) + ZeroOrMore(EDIT_SUB_ELEMENT)) | (INDEXED_SOURCE_ELEMENT)

EDIT_ELEMENT = ((SOURCE_ELEMENT) + ZeroOrMore(EDIT_SUB_ELEMENT)) | (SOURCE_ELEMENT)
                
EDIT_LIST = (TERMINATOR | EDIT_ELEMENT | INDEXED_EDIT_ELEMENT | RETIME_DIRECTIVE | (SYSTEM_DIRECTIVE) | INFORMATIONAL_DIRECTIVE) | Word(NoneOf("\n\r"))

EDL = ZeroOrMore(EDIT_LIST)

# Omitted TRIGGER_ELEMENT | DEVICE_CONTROL_ELEMENT

# create a TimeCode object when we have parsed a TIME_CODE
def TimeCodeSpecifierAction(x) :
  num = len(x)
  h = x[num - 7] if num > 6 else 0
  m = x[num - 5] if num > 4 else 0
  s = x[num - 3] if num > 2 else 0
  f = x[num - 1] if num > 0 else 0

  dropframe = True if num > 1 and x[1] in [';',','] else False
  return TimeCode(h, m, s, f, 0, dropframe)

TIME_CODE_FIELD_SPECIFIER.setAction(TimeCodeSpecifierAction)

# create a TimeCode object when we have parsed a TIME_CODE
def TimeCodeSubFieldSpecifierAction(x) :
  return TimeCode(x[0].hrs(), x[0].mins(), x[0].secs(), x[0].frames(), x[1][0], x[0].isDropFrame())

TIME_CODE_SUB_FIELD_SPECIFIER.setAction(TimeCodeSubFieldSpecifierAction)




"""
SOURCE_ELEMENT.setAction(SourceElementSpecifierAction)

EDIT_ELEMENT.setAction(EditElementSpecifierAction)

DLEDL_ELEMENT.setAction(DLElementSpecifierAction)
#COMMENT_ELEMENT.setAction(DLElementSpecifierAction)
"""

def flatten(q):
    """
    a recursive function that flattens a nested list q
    """
    flat_q = []
    for x in q:
        # may have nested tuples or lists
        if type(x) in (list, tuple):
            flat_q.extend(flatten(x))
        else:
            flat_q.append(x)
    return flat_q
  
   

def dump(p) :
  if p.full():
      print(p.getTokens())
  else:
      print(p.getTokens())
      print('The parser did not consume all input.')
      print(p.getRemaining())
##        print  "\"" + remaining + "\""



import sys
#sys.setrecursionlimit(5000)


def ParseEDL(filename):
  with open(filename, 'r') as file:
    edl = file.read()
  tokens = []
  success = True
  while success:
    try:
      p = parse(EDIT_LIST, edl)
      ptokens = p.getTokens()
      tokens.append(p.getTokens())

      element = None
      if isinstance(ptokens, list):
        element = ptokens[0]
      else:
        element = ptokens

      if isinstance(element, EditDecision) or isinstance(element, RetimeElement):
        element.setSource(p.getConsumed())
      success = True
    except ParseException as e:
      hiero.core.log.exception( "ParseEDL exception: %s", e )
      success = False
    except TypeError as e:
      hiero.core.log.exception( "ParseEDL exception: %s", e )
      raise Exception("Invalid data in file")
    edl = p.getRemaining()
    if len(edl) < 1:
      success = False
  return flatten(tokens)
 
#dump(parse(EDIT_LIST, "470        AX A2    C        00:00:23:13 00:00:24:15 01:14:02:12 01:14:03:14"))


"""
#elements = ParseEDL("/mnt/nethome/users/cherbetji/Smoke v6.53.edl")
#for element in ParseEDL("/mnt/nethome/users/cherbetji/Desktop/Timeline 5.edl"):
elements = ParseEDL("/mnt/nethome/users/cherbetji/edlxml/edit_cmx3600.edl")
#for element in elements:
#  if isinstance(element, EditDecision):
#    print element

print "**********************************"
for element in elements:
  print element


#dump(parse(REAL_NUMBER, '1'))
#dump(parse(REAL_NUMBER, '1.2'))
#dump(parse(REAL_NUMBER, '.43'))
#dump(parse(TIME_CODE_SUB_FIELD_SPECIFIER, '1:23:45:67%4'))
#dump(parse(SOURCE_ELEMENT, '001 043_010 V	C	00:00:00:00 00:00:00:13 00:00:00:00 00:00:00:13'))
#dump(parse(REAL_NUMBER, '2'))
#result = parse(RADIX_NUMBER, '12')
#dump(parse(EDIT_ELEMENT, "TITLE: LR II - The Cradle of Life - POD scene"))
dump(parse(SOURCE_ELEMENT, '001  TAPE1    V     C        01:09:39:22 01:09:50:14 00:08:00:00 00:08:10:17'))
#dump(parse( OneOrMore(PRINTABLE_CHARACTER) , 'MONGO_S1.')) #(104473@104789).DPX'))
#dump(parse( OneOrMore(Literal('\n')) , "\n"))
#dump(parse(EDL, lines) )
"""
