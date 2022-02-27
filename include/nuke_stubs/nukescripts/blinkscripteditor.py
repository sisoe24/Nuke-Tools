import PySide2
import re, sys, traceback, os
import rlcompleter
from io import StringIO
import nuke

#Syntax highlighting colour definitions
kwdsFgColour = PySide2.QtGui.QColor(122, 136, 53)
stringLiteralsFgColourDQ = PySide2.QtGui.QColor(226, 138, 138)
stringLiteralsFgColourSQ = PySide2.QtGui.QColor(110, 160, 121)
commentsFgColour = PySide2.QtGui.QColor(188, 179, 84)
blinkTypesColour = PySide2.QtGui.QColor(25, 25, 80)
blinkFuncsColour = PySide2.QtGui.QColor(3, 185, 191)


#Need to add in the proper methods here
class ScriptInputArea(PySide2.QtWidgets.QPlainTextEdit, PySide2.QtCore.QObject) :

    #Signal that will be emitted when the user has changed the text
    userChangedEvent = PySide2.QtCore.Signal()

    def __init__(self, output, editor, parent=None):
        super(ScriptInputArea, self).__init__(parent)

        # Font will be setup by showEvent function, reading settings from preferences

        #Setup vars
        self._output = output
        self._editor = editor
        self._errorLine = 0
        self._showErrorHighlight = True
        self._completer = None
        self._currentCompletion = None
        self._completerShowing = False
        self._showLineNumbers = True

        self.setStyleSheet("background-color: rgb(81, 81, 81);")

        #Setup completer
        self._completer = PySide2.QtWidgets.QCompleter(self)
        self._completer.setWidget(self)
        self._completer.setCompletionMode(PySide2.QtWidgets.QCompleter.UnfilteredPopupCompletion)
        self._completer.setCaseSensitivity(PySide2.QtCore.Qt.CaseSensitive)
        self._completer.setModel(PySide2.QtCore.QStringListModel())

        #Setup line numbers
        self._lineNumberArea = LineNumberArea(self, parent=self)

        #Add highlighter
        self._highlighterInput = InputHighlighter(self.document(), parent=self)

        #Setup connections
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self._completer.activated.connect(self.insertCompletion)
        self._completer.highlighted.connect(self.completerHighlightChanged)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)

        self.updateLineNumberAreaWidth()
        self._lineNumberArea.setVisible( self._showLineNumbers )
        self.setCursorWidth(PySide2.QtGui.QFontMetricsF(self.font()).width(' '))



    def lineNumberAreaWidth(self) :

        if not self._showLineNumbers :
            return 0

        digits = 1
        maxNum = max(1, self.blockCount())
        while (maxNum >= 10) :
            maxNum /= 10
            digits += 1

        space = 5 + self.fontMetrics().width('9') * digits
        return space


    def updateLineNumberAreaWidth(self) :
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)


    def updateLineNumberArea(self, rect, dy) :
        if (dy) :
            self._lineNumberArea.scroll(0, dy)
        else :
            self._lineNumberArea.update(0, rect.y(), self._lineNumberArea.width(), rect.height())

        if (rect.contains(self.viewport().rect())) :
            self.updateLineNumberAreaWidth()


    def resizeEvent(self, event) :
        PySide2.QtWidgets.QPlainTextEdit.resizeEvent(self, event)

        cr = self.contentsRect()
        self._lineNumberArea.setGeometry(PySide2.QtCore.QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def getFontFromHieroPrefs(self):
        # May raise an ImportError in Nuke standalone
        from hiero.core import ApplicationSettings
        fontStr = ApplicationSettings().value("scripteditor/font")

        # Setup new font and copy settings
        font = PySide2.QtGui.QFont()
        font.fromString(fontStr)
        return font


    def getFontFromNukePrefs(self):
        # Get the font from the preferences for Nuke's Script Editor
        font = PySide2.QtGui.QFont(nuke.toNode("preferences").knob("ScriptEditorFont").value())
        # Set the size, also according to the Script Editor Preferences
        fontSize = nuke.toNode("preferences").knob("ScriptEditorFontSize").getValue()
        font.setPixelSize(fontSize);
        return font


    def setFontFromPrefs(self):
        try:
          font = self.getFontFromHieroPrefs()
        except ImportError:
          font = self.getFontFromNukePrefs()

        # Set the font for the text editor
        self.setFont(font);
        # Make sure the font used for the line numbers matches the text
        self._lineNumberArea.setFont(font);


    def showEvent(self, event):
        PySide2.QtWidgets.QPlainTextEdit.showEvent(self, event)
        self.setFontFromPrefs()


    def lineNumberAreaPaintEvent(self, event) :

        painter = PySide2.QtGui.QPainter(self._lineNumberArea)
        painter.fillRect(event.rect(), self.palette().base())

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int( self.blockBoundingGeometry(block).translated(self.contentOffset()).top() )
        bottom = top + int( self.blockBoundingRect(block).height() )
        currentLine = self.document().findBlock(self.textCursor().position()).blockNumber()

        font = painter.font()
        pen = painter.pen()
        painter.setPen( self.palette().color(PySide2.QtGui.QPalette.Text) )

        while (block.isValid() and top <= event.rect().bottom()) :

            if (block.isVisible() and bottom >= event.rect().top()) :

                if ( blockNumber == currentLine ) :
                    painter.setPen(PySide2.QtGui.QColor(255, 255, 255))
                    font.setBold(True)
                    painter.setFont(font)

                elif ( blockNumber == int(self._errorLine) - 1 ) :
                    painter.setPen(PySide2.QtGui.QColor(127, 0, 0))
                    font.setBold(True)
                    painter.setFont(font)

                else :
                    painter.setPen(PySide2.QtGui.QColor(35, 35, 35))
                    font.setBold(False)
                    painter.setFont(font)

                number = "%s" % str(blockNumber + 1)
                painter.drawText(0, top, self._lineNumberArea.width(), self.fontMetrics().height(), PySide2.QtCore.Qt.AlignRight, number)

            #Move to the next block
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1


    def highlightCurrentLine(self) :

        extraSelections = []

        if (self._showErrorHighlight and not self.isReadOnly()) :
            selection = PySide2.QtWidgets.QTextEdit.ExtraSelection()

            lineColor = PySide2.QtGui.QColor(255, 255, 255, 40)

            selection.format.setBackground(lineColor)
            selection.format.setProperty(PySide2.QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()

            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)
        self._errorLine = 0


    def highlightErrorLine(self) :

        extraSelections = []

        if (self._showErrorHighlight and not self.isReadOnly()) :
            if (self._errorLine != 0) :
                selection = PySide2.QtWidgets.QTextEdit.ExtraSelection()

                selection.format.setBackground(PySide2.QtGui.QColor(255, 0, 0, 40))
                selection.format.setProperty(PySide2.QtGui.QTextFormat.OutlinePen, PySide2.QtGui.QPen(PySide2.QtGui.QColor(127, 0, 0, 0)))
                selection.format.setProperty(PySide2.QtGui.QTextFormat.FullWidthSelection, True)

                pos = self.document().findBlockByLineNumber(int(self._errorLine)-1).position()
                cursor = self.textCursor()
                cursor.setPosition(pos)

                selection.cursor = cursor
                selection.cursor.clearSelection()
                extraSelections.append(selection)

        self.setExtraSelections(extraSelections)

    def keyPressEvent(self, event) :

        lScriptEditorMod = ((event.modifiers() and (PySide2.QtCore.Qt.ControlModifier or PySide2.QtCore.Qt.AltModifier)) == PySide2.QtCore.Qt.ControlModifier)
        lScriptEditorShift = ((event.modifiers() and (PySide2.QtCore.Qt.ShiftModifier)) != 0)
        lKey = event.key()

        #TODO Query Completer Showing
        self._completerShowing = self._completer.popup().isVisible()

        if not self._completerShowing :
            if (lScriptEditorMod and (lKey == PySide2.QtCore.Qt.Key_Return or lKey == PySide2.QtCore.Qt.Key_Enter)) :
              if (self._editor) :
                self._editor.runScript()
              return
            #elif lScriptEditorMod and lScriptEditorShift and lKey == PySide2.QtCore.Qt.Key_BraceLeft :
            #    self.decreaseIndentationSelected()
            #    return
            #elif lScriptEditorMod and lScriptEditorShift and lKey == PySide2.QtCore.Qt.Key_BraceRight :
            #    self.increaseIndentationSelected()
            #    return
            elif lScriptEditorMod and lKey == PySide2.QtCore.Qt.Key_Slash :
                self.commentSelected()
                return
            elif lScriptEditorMod and lKey == PySide2.QtCore.Qt.Key_Backspace :
                self._editor.clearOutput()
                return
            elif lKey == PySide2.QtCore.Qt.Key_Tab or (lScriptEditorMod and lKey == PySide2.QtCore.Qt.Key_Space) :
                #Ok.
                #If you have a selection you should indent
                #ElIf line is blank it should always pass through the key event
                #Else get the last
                tc = self.textCursor()
                if tc.hasSelection() :
                    print("Indenting")
                    self.increaseIndentationSelected()
                else :
                    #Show completion
                    colNum = tc.columnNumber()
                    posNum = tc.position()
                    inputText = self.toPlainText()
                    inputTextToCursor = self.toPlainText()[0:posNum]
                    inputTextSplit = inputText.splitlines()
                    inputTextToCursorSplit = inputTextToCursor.splitlines()
                    runningLength = 0
                    currentLine = None

                    for line in inputTextToCursorSplit :
                        length = len(line)
                        runningLength += length
                        if runningLength >= posNum :
                            currentLine = line
                            break
                        runningLength += 1

                    if currentLine :

                        if len(currentLine.strip()) == 0 : 
                           tc = self.textCursor()
                           tc.insertText("  ")
                           return

                        token = currentLine.split(" ")[-1]
                        if "(" in token :
                            token = token.split("(")[-1]

                        if len(token)>0:
                            self.completeTokenUnderCursor(token)
                        else :
                            tc = self.textCursor()
                            tc.insertText("  ")
                    else :
                        tc = self.textCursor()
                        tc.insertText("  ")

                    #print mid(tc.position() - tc.columnNumber(), tc.columnNumber())

            else :
                PySide2.QtWidgets.QPlainTextEdit.keyPressEvent(self, event)
                return
        else :
            tc = self.textCursor()
            if lKey == PySide2.QtCore.Qt.Key_Return or lKey == PySide2.QtCore.Qt.Key_Enter :
                self.insertCompletion(self._currentCompletion)
                self._currentCompletion = ""
                self._completer.popup().hide()
                self._completerShowing = False
            elif lKey == PySide2.QtCore.Qt.Key_Right or lKey == PySide2.QtCore.Qt.Key_Escape:
                self._completer.popup().hide()
                self._completerShowing = False
            elif lKey == PySide2.QtCore.Qt.Key_Tab or (lScriptEditorMod and lKey == PySide2.QtCore.Qt.Key_Space) :
                self._currentCompletion = ""
                self._completer.popup().hide()
            else :
                PySide2.QtWidgets.QPlainTextEdit.keyPressEvent(self, event)
                #Edit completion model
                colNum = tc.columnNumber()
                posNum = tc.position()
                inputText = self.toPlainText()
                inputTextSplit = inputText.splitlines()
                runningLength = 0
                currentLine = None
                for line in inputTextSplit :
                    length = len(line)
                    runningLength += length
                    if runningLength >= posNum :
                        currentLine = line
                        break
                    runningLength += 1
                if currentLine :
                    token = currentLine.split(" ")[-1]
                    if "(" in token :
                            token = token.split("(")[-1]
                    self.completeTokenUnderCursor(token)
                #PySide2.QtWidgets.QPlainTextEdit.keyPressEvent(self, event)
                return

    def focusOutEvent(self, event):
      self.userChangedEvent.emit()
      return



    def insertIndent(self, tc) :

        tc.beginEditBlock()
        tc.insertText("\t")
        tc.endEditBlock

    def commentSelected(self) :

        return

        tc = self.textCursor();
        if tc.hasSelection() :

            tc.beginEditBlock()
            self.ExtendSelectionToCompleteLines(tc)
            start = tc.selectionStart()
            end = tc.selectionEnd()
            tc.setPosition(start)


            if self.document().characterAt(start) == '#' :

              #Comment
              print("Uncommenting")
              # prevPosition = end
              # while tc.position() != prevPosition  :
              #   tc.insertText("#");
              #   prevPosition = tc.position()
              #   tc.movePosition(PySide2.QtGui.QTextCursor.NextBlock, PySide2.QtGui.QTextCursorMoveAnchor)

            else :

              #Uncomment
              print("Commenting")
              # prevPosition = end
              # while tc.position() != prevPosition  :
              #   if self.document().characterAt(tc.position()) == '#' :
              #     tc.deleteChar()
              #     prevPosition = tc.position()
              #     tc.movePosition(PySide2.QtGui.QTextCursor.NextBlock, PySide2.QtGui.QTextCursor.MoveAnchor)

              #self.select(start, tc.position())
              #tc.endEditBlock()
              #self.ensureCursorVisible()

    def ExtendSelectionToCompleteLines(self, tc) :

        lPos    = tc.position()
        lAnchor = tc.anchor()
        tc.setPosition(tc.anchor());

        if (lPos >= lAnchor) :
          print("Moving to start of line")
          #Position was after the anchor.  Move to the start of the line,
          tc.movePosition(PySide2.QtGui.QTextCursor.StartOfLine)
          tc.setPosition(lPos, PySide2.QtGui.QTextCursor.KeepAnchor)
          #Don't extend if the position was at the beginning of a new line
          lSelected = tc.selectedText()
          if lSelected != "" and lSelected[-2:-1] != "\n" :
            tc.movePosition(PySide2.QtGui.QTextCursor.EndOfLine, PySide2.QtGui.QTextCursor.KeepAnchor)

        else :
          print("Moving to end of line")
          #Position was before the anchor.  Move to the end of the line,
          #then select to the start of the line where the position was.
          #Don't select to the end of the current line if the anchor was at the beginning
          tc.movePosition(PySide2.QtGui.QTextCursor.PreviousCharacter,PySide2.QtGui.QTextCursor.KeepAnchor)
          lSelected = tc.selectedText()
          tc.movePosition(PySide2.QtGui.QTextCursor.NextCharacter)
          if lSelected != "" and lSelected[-2:-1] != "\n" :
            tc.movePosition(PySide2.QtGui.QTextCursor.EndOfLine)
          tc.setPosition(lPos, PySide2.QtGui.QTextCursor.KeepAnchor)
          tc.movePosition(PySide2.QtGui.QTextCursor.StartOfLine, PySide2.QtGui.QTextCursor.KeepAnchor)


    def increaseIndentationSelected(self) :

        print("Need to fix indenting")

        return

        tc = self.textCursor()
        if tc.hasSelection() :
            start = tc.selectionStart()
            self.ExtendSelectionToCompleteLines(tc)
            selected = tc.selectedText()

            self.insertIndent(tc)

            #replace paragraph things here
            paraReplace = "\n" + ("\t")
            indentedParas = selected.replace('\n', paraReplace)

            textSplit = selected.splitlines()
            indentedText = paraReplace.join(textSplit)

            tc.beginEditBlock()
            tc.removeSelectedText()
            tc.insertText(indentedText)
            tc.endEditBlock()

            print("Need to fix selection after indenting")

            self.setTextCursor(tc)



            end = tc.selectionEnd()

            tc.setPosition(start)
            tc.setPosition(end, PySide2.QtGui.QTextCursor.KeepAnchor)



            self.ensureCursorVisible()

    def decreaseIndentationSelected(self):
        print("Need to fix unindenting")
        return

        tc = self.textCursor()
        if (tc.hasSelection()) :
            start = tc.selectionStart()
            self.ExtendSelectionToCompleteLines(tc)
            return
            selected = tc.selectedText()

            #Get rid of indents
            textSplit = selected.splitlines()
            unsplitLines = []
            unindentedText = selected

            for line in textSplit :
                print(type(line))
                unsplitLines.append(line.replace('\t', '', 1))

            unindentedText = "\n".join(unsplitLines)

            tc.beginEditBlock()
            tc.removeSelectedText()
            tc.insertText(unindentedText)
            tc.endEditBlock()
            end = tc.selectionEnd()

            tc.setPosition(start)
            tc.setPosition(end, PySide2.QtGui.QTextCursor.KeepAnchor)

            #tc.select(start, tc.position())

            self.setTextCursor(tc)

            self.ensureCursorVisible()

    def completionsForToken(self, token):
        comp = rlcompleter.Completer()
        completions = []
        completion = 1
        for x in range(0, 1000):
            completion = comp.complete(token, x)
            if completion is not None:
                completions.append(completion)
            else :
                break
        return completions

    def completeTokenUnderCursor(self, token) :

        #Clean token
        token = token.lstrip().rstrip()

        completionList = self.completionsForToken(token)
        if len(completionList) == 0 :
            return

        #Set model for _completer to completion list
        self._completer.model().setStringList(completionList)

        #Set the prefix
        self._completer.setCompletionPrefix(token)

        #Check if we need to make it visible
        if self._completer.popup().isVisible() :
            rect = self.cursorRect();
            rect.setWidth(self._completer.popup().sizeHintForColumn(0) + self._completer.popup().verticalScrollBar().sizeHint().width())
            self._completer.complete(rect)
            return

        #Make it visible
        if len(completionList) == 1 :
            self.insertCompletion(completionList[0]);
        else :
            rect = self.cursorRect();
            rect.setWidth(self._completer.popup().sizeHintForColumn(0) + self._completer.popup().verticalScrollBar().sizeHint().width())
            self._completer.complete(rect)

        return

    def insertCompletion(self, completion):
        if completion :
            completionNoToken = completion[len(self._completer.completionPrefix()):]
            lCursor = self.textCursor()
            lCursor.insertText(completionNoToken)
        return

    def completerHighlightChanged(self, highlighted):
        self._currentCompletion = highlighted

# void ScriptInputArea::insertCompletion(const QString& completion)
# {
#   QString suffix = completion;
#   suffix.remove(0, _completer->completionPrefix().length());
#   QTextCursor lCursor = textCursor();
#   lCursor.insertText(suffix);
# }

    def getErrorLineFromTraceback(self, tracebackStr) :
        finalLine = None
        for line in tracebackStr.split('\n') :
            if 'File "<string>", line' in line :
                finalLine = line
        if finalLine == None :
            return 0
        try :
            errorLine = finalLine.split(',')[1].split(' ')[2]
            return errorLine
        except :
            return 0

    def runScript(self):
        _selection = False;
        self.highlightCurrentLine()

        #Get text
        text = self.toPlainText()

        #Check if we've got some text selected. If so, replace text with selected text
        tc = self.textCursor()
        if tc.hasSelection() :
            _selection = True
            rawtext = tc.selectedText()
            rawSplit = rawtext.splitlines()
            rawJoined = '\n'.join(rawSplit)
            text = rawJoined.lstrip().rstrip()

        #Fix syntax error if last line is a comment with no new line
        if not text.endswith('\n') :
            text = text + '\n'

        #JERRY has a lock here

        #Compile
        result = None
        compileSuccess = False
        runError = False

        try :
            compiled = compile(text, '<string>', 'exec')
            compileSuccess = True
        except Exception as e:
            result = traceback.format_exc()
            runError = True
            compileSuccess = False

        oldStdOut = sys.stdout
        if compileSuccess :
            #Override stdout to capture exec results
            buffer = StringIO()
            sys.stdout = buffer
            try :
                exec(compiled, globals())
            except Exception as e:
                runError = True
                result = traceback.format_exc()
            else :
                result = buffer.getvalue()
        sys.stdout = oldStdOut
        #print "STDOUT Restored"

        #Update output
        self._output.updateOutput( text )
        self._output.updateOutput( "\n# Result: \n" )
        self._output.updateOutput( result )
        self._output.updateOutput( "\n" )

        if runError :
            #print "There was an error"
            #print "result is %s " % result
            self._errorLine = self.getErrorLineFromTraceback(result)
            self.highlightErrorLine()

#Need to add in the proper methods here
class InputHighlighter(PySide2.QtGui.QSyntaxHighlighter) :
    def __init__(self, doc, parent=None):

        super(InputHighlighter, self).__init__(parent)

        self.setDocument(doc)

        self._rules = []
        self._keywords = PySide2.QtGui.QTextCharFormat()
        self._strings = PySide2.QtGui.QTextCharFormat()
        self._stringSingleQuotes = PySide2.QtGui.QTextCharFormat()
        self._comment = PySide2.QtGui.QTextCharFormat()
        self._blinkFuncs = PySide2.QtGui.QTextCharFormat()
        self._blinkTypes = PySide2.QtGui.QTextCharFormat()

        self._keywords.setForeground(kwdsFgColour)
        self._keywords.setFontWeight(PySide2.QtGui.QFont.Bold)

        #Construct rules for C++ keywords
        #keywordPatterns = ["\\bchar\\b" , "\\bclass\\b" , "\\bconst\\b"
        #             , "\\bdouble\\b" , "\\benum\\b" , "\\bexplicit\\b"
        #             , "\\bfriend\\b" , "\\binline\\b" , "\\bint\\b"
        #             , "\\blong\\b" , "\\bnamespace\\b" , "\\boperator\\b"
        #             , "\\bprivate\\b" , "\\bprotected\\b" , "\\bpublic\\b"
        #             , "\\bshort\\b" , "\\bsignals\\b" , "\\bsigned\\b"
        #             , "\\bslots\\b" , "\\bstatic\\b" , "\\bstruct\\b"
        #             , "\\btemplate\\b" , "\\btypedef\\b" , "\\btypename\\b"
        #             , "\\bunion\\b" , "\\bunsigned\\b" , "\\bvirtual\\b"
        #             , "\\bvoid\\b" , "\\bvolatile\\b"]
        #Construct rules for RIP++ keywords
        keywordPatterns = ["\\bchar\\b" ,
                           "\\bclass\\b" ,
                           "\\bconst\\b" ,
                           "\\bdouble\\b" ,
                           "\\benum\\b" ,
                           "\\bexplicit\\b" ,
                           "\\bfriend\\b" ,
                           "\\binline\\b" ,
                           "\\bint\\b" ,
                           "\\blong\\b" ,
                           "\\bnamespace\\b" ,
                           "\\boperator\\b" ,
                           "\\bprivate\\b" ,
                           "\\bprotected\\b" ,
                           "\\bpublic\\b" ,
                           "\\bshort\\b" ,
                           "\\bsigned\\b" ,
                           "\\bstatic\\b" ,
                           "\\bstruct\\b" ,
                           "\\btemplate\\b" ,
                           "\\btypedef\\b" ,
                           "\\btypename\\b" ,
                           "\\bunion\\b" ,
                           "\\bunsigned\\b" ,
                           "\\bvirtual\\b" ,
                           "\\bvoid\\b" ,
                           "\\bvolatile\\b",
                           "\\blocal\\b",
                           "\\bparam\\b",
                           "\\bkernel\\b",
                           ]

        for pattern in keywordPatterns:
          rule = {}
          rule['pattern'] = pattern
          rule['format'] = self._keywords
          self._rules.append(rule)

        #Blink funcs
        self._blinkFuncs.setForeground(blinkFuncsColour)
        #self._blinkFuncs.setFontWeight(PySide2.QtGui.QFont.Bold)
        blinkFuncPatterns = ["\\bdefine\\b" ,
                             "\\bdefineParam\\b" ,
                             "\\bprocess\\b" ,
                             "\\binit\\b" ,
                             "\\bsetRange\\b" ,
                             "\\bsetAxis\\b" ,
                             "\\bmedian\\b" ,
                             "\\bbilinear\\b" ,
                           ]
        for pattern in blinkFuncPatterns:
          rule = {}
          rule['pattern'] = pattern
          rule['format'] = self._blinkFuncs
          self._rules.append(rule)

        #Blink types
        self._blinkTypes.setForeground(blinkTypesColour)
        #self._blinkTypes.setFontWeight(PySide2.QtGui.QFont.Bold)
        blinkTypesPatterns = ["\\bImage\\b" ,
                             "\\beRead\\b" ,
                             "\\beWrite\\b" ,
                             "\\beEdgeClamped\\b" ,
                             "\\beEdgeConstant\\b" ,
                             "\\beEdgeNull\\b" ,
                             "\\beAccessPoint\\b" ,
                             "\\beAccessRanged1D\\b" ,
                             "\\beAccessRanged2D\\b" ,
                             "\\beAccessRandom\\b" ,
                             "\\beComponentWise\\b" ,
                             "\\bePixelWise\\b" ,
                             "\\bImageComputationKernel\\b" ,
                             "\\bint\\b" ,
                             "\\bint2\\b" ,
                             "\\bint3\\b" ,
                             "\\bint4\\b" ,
                             "\\bfloat\\b" ,
                             "\\bfloat2\\b" ,
                             "\\bfloat3\\b" ,
                             "\\bfloat4\\b" ,
                             "\\bfloat3x3\\b" ,
                             "\\bfloat4x4\\b" ,
                             "\\bbool\\b" ,
                            ]
        for pattern in blinkTypesPatterns:
          rule = {}
          rule['pattern'] = pattern
          rule['format'] = self._blinkTypes
          self._rules.append(rule)

        #String Literals
        self._strings.setForeground(stringLiteralsFgColourDQ)
        rule = {}
        rule['pattern'] = "\"([^\"\\\\]|\\\\.)*\""
        rule['format'] = self._strings
        self._rules.append(rule)

        #String single quotes
        self._stringSingleQuotes.setForeground(stringLiteralsFgColourSQ)
        rule = {}
        rule['pattern'] = "'([^'\\\\]|\\\\.)*'"
        rule['format'] = self._stringSingleQuotes
        self._rules.append(rule)

        #Comments
        self._comment.setForeground(commentsFgColour)
        rule = {}
        rule['pattern'] = "//[^\n]*"
        rule['format'] = self._comment
        self._rules.append(rule)



    def highlightBlock(self, text) :

        text = str(text)

        for rule in self._rules :
            expression = rule['pattern']

            if len(text) > 0 :
                results = re.finditer(expression, text)

                #Loop through all results
                for result in results :
                    index = result.start()
                    length = result.end() - result.start()
                    self.setFormat(index, length, rule['format'])

class LineNumberArea(PySide2.QtWidgets.QWidget):
    def __init__(self, scriptInputWidget, parent=None):
        super(LineNumberArea, self).__init__(parent)

        self._scriptInputWidget = scriptInputWidget
        #self.setStyleSheet("QWidget { background-color: blue; }");
        self.setStyleSheet("text-align: center;")

    def sizeHint(self) :
        return PySide2.QtCore.QSize(self._scriptInputWidget.lineNumberAreaWidth(), 0)

    def paintEvent(self, event) :
        self._scriptInputWidget.lineNumberAreaPaintEvent(event)
        return
