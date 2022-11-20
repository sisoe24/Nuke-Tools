# Copyright (c) 2019 The Foundry Visionmongers Ltd.  All Rights Reserved.
# This file contains audio constants used by the audio and transcode exporters,

from collections import OrderedDict

# Channel layout keys
kMonoLayout = 'mono'
kStereoLayout = 'stereo'
kFivePointOneLayout = '5.1 (L R C LFE Ls Rs)'
kSevenPointOneLayout ='7.1 (L R C LFE Ls Rs Bsl Bsr)'

# Codec keys
kPCMCodec = 'linear PCM (wav)'
kMP2Codec = 'MP2'
kAC3Codec = 'AC-3'
kAACCodec = 'AAC'

# Sample rate keys
k44100Key = '44100 Hz'
k48khzKey = '48000 Hz'
k96khzKey = '96000 Hz'

# Bit depth keys
k16bitKey = '16 bit'
k24bitKey = '24 bit'
k32bitKey = '32 bit (float)'

# Bit rate keys
k192kbpsKey = '192 kbp/s'
k256kbpsKey = '256 kbp/s'
k320kbpsKey = '320 kbp/s'

# Preset keys
kNumChannelsKey = "numChannels"
kCodecKey = "codec"
kSampleRateKey = "sampleRate"
kBitDepthKey = "bitDepth"
kBitRateKey = "bitRate"

# Defaults
kDefaultChannels = kStereoLayout
kNonCompressedCodec = kPCMCodec
kDefaultCodec = kNonCompressedCodec
kDefaultSampleRate = k44100Key
kDefaultBitDepth = k24bitKey
kDefaultBitRate = k320kbpsKey

# Dictionaries
kChannels = OrderedDict ([(kMonoLayout, 1), (kStereoLayout, 2), (kFivePointOneLayout, 6), (kSevenPointOneLayout, 8)])
# Note: the compressed codecs have been left commented out for the time being. When TP 420613 and TP 410681 are resolved,
# the additional codecs here should be uncommented.
kCodecs = OrderedDict ([(kPCMCodec, '.wav')])#, (kAACCodec, '.m4a') #, (kMP2Codec, '.mp2'), (kAC3Codec, '.ac3')])
kSampleRates = OrderedDict ([(k44100Key, 44100), (k48khzKey, 48000), (k96khzKey, 96000)])
# 96k not supported by mp2/ac3
kCompressedSampleRates = OrderedDict ([(k44100Key, 44100), (k48khzKey, 48000)])
kBitDepths = OrderedDict ([(k16bitKey, 16), (k24bitKey, 24), (k32bitKey, 32)])
kBitRates = OrderedDict ([(k192kbpsKey, 192000), (k256kbpsKey, 256000), (k320kbpsKey, 320000)])
