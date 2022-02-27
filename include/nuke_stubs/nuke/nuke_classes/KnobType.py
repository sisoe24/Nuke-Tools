from numbers import Number
from typing import *

import nuke
from . import *

class KnobType(object):
    """
    Constants for use in parameters which require a knob type.
    """
    eObsoleteKnob = 0
    eStringKnob = 1
    eFileKnob = 2
    eIntKnob = 3
    eEnumKnob = 4
    eBitMaskKnob = 5
    eBoolKnob = 6
    eDoubleKnob = 7
    eFloatKnob = 8
    eArrayKnob = 9
    eChannelMaskKnob = 10
    eChannelKnob = 11
    eXYKnob = 12
    eXYZKnob = 13
    eWHKnob = 14
    eBBoxKnob = 15
    eSizeKnob = 16
    eFormatKnob = 17
    eColorKnob = 18
    eAColorKnob = 19
    eTabKnob = 20
    eCustomKnob = 21
    ePyScriptKnob = 22
    eTextEditorKnob = 23
    eTransform2DKnob = 24
    eSpacerKnob = 25
    eTextKnob = 26
    eHelpKnob = 27
    eMultilineStringKnob = 28
    eAxisKnob = 29
    eUVKnob = 30
    eBox3Knob = 31
    eScriptKnob = 32
    eLookupCurvesKnob = 33
    eTooltipKnob = 34
    ePulldownKnob = 35
    eEyeDropperKnob = 36
    eRangeKnob = 37
    eHistogramKnob = 38
    eKeyerKnob = 39
    eColorChipKnob = 40
    eLinkKnob = 41
    eScaleKnob = 42
    eMultilineEvalStringKnob = 43
    eOneViewKnob = 44
    eMultiViewKnob = 45
    eViewViewKnob = 46
    ePyPulldownKnob = 47
    eMultiArrayKnob = 49
    eViewPairKnob = 50
    eListKnob = 51
    ePythonKnob = 52
    eMetaDataKnob = 53
    ePixelAspectKnob = 54
    eCpKnob = 55
    eToolbarKnob = 56
    eTabGroupKnob = 57
    ePluginPythonKnob = 58
    eExoGroupKnob = 59
    eMenuKnob = 60
    ePasswordKnob = 61
    eToolboxKnob = 62
    eTableKnob = 63
    eGeoSelectKnob = 64
    eInputOnlyChannelMaskKnob = 65
    eInputOnlyChannelKnob = 66
    eControlPointCollectionKnob = 67
    eCascadingEnumerationKnob = 68
    eDynamicBitmaskKnob = 69
    eMetaKeyFrameKnob = 70
    ePositionVectorKnob = 71
    eCachedFileKnob = 72
    eTransformJackKnob = 73
    eRippleKnob = 74
    eSceneViewKnob = 75
    eVSpacerKnob = 76
    eCancelExecutionKnob = 77
    eSimpleArrayKnob = 78
    eResizableArrayKnob = 79
    eDisableKnob = 80
    eIconKnob = 81
    eFrameExtentKnob = 82
    eRadioKnob = 83
    eFreeTypeKnob = 84
    eEditableEnumerationKnob = 85
    eColorspaceKnob = 86
    eParticleChannelsKnob = 87
    eSceneGraphKnob = 88
    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None