#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . events import (registerInterest, EventType)
from . FnEffectHelpers import transformSequenceEffectsToFormat


def onSequenceFormatChanged(event):

  def errorCallback(message):
    print("onSequenceFormatChanged error:", message)

  transformSequenceEffectsToFormat(event.sequence,
                                   event.format,
                                   event.oldFormat,
                                   errorCallback)


# Register callback
registerInterest(EventType.kSequenceFormatChanged, onSequenceFormatChanged)
