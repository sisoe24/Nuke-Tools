# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke

singleLineInput = None
filenameSearch = None
clipnameSearch = None
multilineTextInput = None
notepad = None
booleanCheckBox = None
rgbColorChip = 0x0
enumerationPulldown = "first second third"
textFontPulldown = None
expressionInput = "[python -eval 3*2]"

def panel_example():
  p = nuke.Panel("Test Panel")
  p.addSingleLineInput("Single Line Input:", singleLineInput)
  p.addSingleLineInput("Second Line Input:", singleLineInput)
  p.addPasswordInput("Password Input:", singleLineInput)
  p.addFilenameSearch("Filename Search:", filenameSearch)
  p.addClipnameSearch("Clipname Search:", clipnameSearch)
  p.addMultilineTextInput("Multiline Text Input:", multilineTextInput)
  p.addNotepad("Notepad:", notepad)
  p.addBooleanCheckBox("Boolean Check Box:", booleanCheckBox)
  p.addRGBColorChip("RGB Color Chip:", rgbColorChip)
  p.addEnumerationPulldown("Enumeration Pulldown:", enumerationPulldown)
  p.addTextFontPulldown("Text Font Pulldown:", textFontPulldown)
  p.addExpressionInput("Expression Input:", expressionInput)
  p.addButton("Cancel")
  p.addButton("OK")
  result = p.show()

  filenameVal= p.value("Filename Search:")
  if filenameVal is not None:
    print("filename:", filenameVal)

  colorVal = p.value("RGB Color Chip:")
  if colorVal is not None:
    print("rgbColorChip: ", hex(colorVal))

  enumVal = p.value("Enumeration Pulldown:")
  if enumVal is not None:
    print("Enumeration Pulldown: ", enumVal)

  boolVal = p.value("Boolean Check Box:")
  if boolVal is not None:
    print("Boolean Check Box:", boolVal)

  textFontVal = p.value("Text Font Pulldown:")
  if textFontVal is not None:
    print("Text Font Pulldown:", textFontVal)

  exprVal = p.value("Expression Input:")
  if exprVal is not None:
    print("Expression Input:", exprVal)

