"""
Parsing framework in Python, similar to pyparsing and boost::spirit

Author: Markus Brueckner (dev@slash-me.net)

License: This code is in the public domain

FAQ:
What's 'yeanpypa' anyway?

YEt ANother PYthon PArser framework. Virtually perfectly creative acronym...
"""
import logging

class InputReader(object):
    """
    The InputReader serves as an abstraction to read chars from a
    string with a state. The reader provides tools to save the current
    reading position and a stack to set checkpoints where to return to
    later.
    """

    def __init__(self, string, ignore_white):
        """
        Create this reader with the given string.

        @param string: The string the reader reads from.
        @type  string: str
        @param ignore_white: Whether to ignore whitespaces or not.
        @type  ignore_white: boolean
        """
        self.__current_pos  = 0
        self.__stack        = []
        self.__string       = string
        self.__ignore_white = ignore_white

    def getPos(self):
        """
        Return the current position of this reader

        @return: the current position of the reader in the string
        """
        return self.__current_pos

    def skipWhite(self):
        """
        Function to skip the whitespace characters from the current position on.
        """
        while (self.__current_pos < len(self.__string) and self.__string[self.__current_pos].isspace()):
            self.__current_pos += 1            
        

    def getString(self,length):
        """
        Get a substring of the string from this reader and advance the reader's position.
        This method returns the current substring of the reader with the given length.
        Note that even if ignore_whitespace is True, the string will return any containing
        whitespaces.

        @param length: The length of the string to return
        @type  length: int
        @return:       A substring of the given length.
        """
        if length == -1:
           return self.__string
        if self.__ignore_white:
            self.skipWhite()
        if self.__current_pos+length > len(self.__string):
            raise EndOfStringException()
        start = self.__current_pos
        self.__current_pos += length
        return self.__string[start:self.__current_pos]

    def getChar(self):
        """
        Get a single character from the string.
        This methdo returns the next character of the string. If ignore_whitespace
        is True, this will be the next non-whitespace character.

        @return: The next character of the string.
        """
        if self.__ignore_white:
            self.skipWhite()
            logging.debug("Getting char at position %d" % self.__current_pos)
        if self.__current_pos == len(self.__string):
            raise EndOfStringException()
        logging.debug("Getting char at position %d" % self.__current_pos)
        char = self.__string[self.__current_pos]
        self.__current_pos += 1
        return char

    def checkPoint(self):
        """
        Set a checkpoint in the reader. A checkpoint is kind of like a safety net where
        the parser can return to later if parsin failed at any later point in the string.
        The checkpoints are managed in a stack-like fashion: the parser can always return
        to the last checkpoint set.
        """
        self.__stack.append(self.__current_pos)

    def rollback(self):
        """
        Rollback the parser to the last checkpoint set. This is called
        by the rules internally whenever parsing fails and a rollback
        is necessary.
        """
        if len(self.__stack) == 0:
            raise EmptyStackException()
        self.__current_pos = self.__stack[-1]
        self.__stack = self.__stack[:-1]

    def deleteCheckpoint(self):
        """
        Delete the newest checkpoint without rolling back. If a rules
        sucessfully matches, it deletes the previously saved
        checkpoint to clean up the parser stack
        """
        if len(self.__stack) == 0:
            raise EmptyStackException()
        self.__stack = self.__stack[:-1]

    def fullyConsumed(self):
        """
        Return whether the string was fully consumed

        @return: True if the string was read to the last byte, False otherwise
        """
        return len(self.__string) == self.__current_pos

    def getIgnoreState(self):
        """
        Return whether the reader is set to ignore whitespaces.

        @return: True if the reader currently ignores whitespaces, False otherwise.
        """
        return self.__ignore_white

    def setIgnoreState(self, state):
        """
        Set the ignore state of the reader. This call tells the reader whether it should ignore whitespaces or not.

        @param state: True to ignore whitespace, False to return them
        @type  state: boolean
        """
        self.__ignore_white = state

class ParseException(Exception):
    """
    An exception thrown on parser error. This exception is thrown by
    the parser in case of a non-correctable error. It contains a human
    readable message that further explains the reason of the
    exception.
    """
    def __init__(self, msg):
        """
        Initialize the exception with the given message.

        @param msg: The message further describing the reason for this exception.
        @type msg:  str
        """
        self.__msg = msg

    def __str__(self):
        """
        Return a human readable representation of this exceptions

        @return: a human readable representation of the exception.
        """
        return "ParseException: %s" % self.__msg

class EndOfStringException(Exception):
    """
    Exception used internally by the InputReader to signal the end of
    the input string.
    """
    pass

class ParseResult(object):
    """
    The class representing the result of a parser run. An object of
    this class is returned by the parse() function. The ParseResult
    contains information about whether the parsing fully consumed the
    string and a list of token generated by the parser.
    """    
    def __init__(self, input_reader, token):
        """
        Initialize the result object with the input reader and the token list.

        @param input_reader: The InputReader used by the parser.
        @type  input_reader: InputReader
        @param token: The list of tokens generated by the parser.
        @type  token: list
        """
        self.__input_reader = input_reader
        self.__token = token

    def full(self):
        """
        Check whether the input was fully consumed.

        @return True if the input was fully consumed, False otherwise.
        """
        return self.__input_reader.fullyConsumed()

    def getTokens(self):
        """
        Return the list of token generated by the parser.

        @return: A list of token generated by the parser.
        """
        return self.__token
    
    def getRemaining(self):
        """ 
        Return the remaining string of a result that wasn't fully consumed 
        """
        return self.__input_reader.getString(-1)[self.__input_reader.getPos():]

    def getConsumed(self):
        """
        Return string conumed in the parse
        """
        return self.__input_reader.getString(-1)[0:self.__input_reader.getPos()]
        
class Rule(object):
    """
    The basic entity of a grammar: the rule.  This class doesn't
    provide any parsing functionality on it's own. It merely provides
    some basic functions shared by all Rule classes.
    """
    action     = None
    hide_token = False

    def match(input_reader):
        """
        Match the given rule in the string from the given position on.

        @param input_reader: The InputReader to read the input from.
        @type  input_reader: InputReader
        @return: a list of token the rule matched.
        """
        pass

    def __add__(self, second_rule):
        """
        Define an operator to concat two rules. The expressivness of
        the 'pseudo-language' defined by the framework heavily relies
        on operator overloading. The +-operator serves as a 'followed
        by' expression.

        @param second_rule: The right operand of the +-operator which
                            follows this object in grammar terms.
        @type  second_rule: Rule
        @return An AndRule-object connecting these two rule appropriately.
        """
        return AndRule(self, second_rule)

    def __or__(self, second_rule):
        """
        Define an operator to concat two rules via OR. The
        expressivness of the 'pseudo-language' defined by the
        framework heavily relies on operator overloading. The
        |-operator serves as a 'OR' expression, defining two
        alternative matches.

        @param second_rule: The right operand of the +-operator which
                            follows this object in grammar terms.
        @type  second_rule: Rule
        @return An OrRule-object connecting these two rule appropriately.
        """
        return OrRule(self, second_rule)

    def setAction(self, action):
        """
        Set the action to execute on a rule match. Action may be any callable
        that takes a one parameter. The parameter is a list of token the rule
        matched. The action may manipulate the token returned by returning
        a different token list.

        @param action: The callable to execute if the rule matched.
        @type  action: Callable
        @return: a reference to the rule itself
        """
        self.action = action
        return self

    def callAction(self, param):
        """
        Call the action attached to this rule. The given parameter is passed to
        the action.

        @param param: The parameter (token list) to pass to the action.
        @type  param: list
        """
        if self.action:
            if isinstance(param, list):
                return self.action(param)
            else:
                return self.action([param])
        else:
            return param

    def hide(self):
        """
        Tell this rule to not produce any token output. The rule
        matches its token as normal but does not return any of them

        @return self
        """
        self.hide_token = True
        return self

    def returnToken(self, token):
        """
        Helper function encapsulating the hide()-functionality. This method
        returns the token if self.hide is False and None otherwise.

        @param token: The toden to return
        @return: token if self.hide==False, None otherwise
        """
        if self.hide_token:
            return None
        else:
            return token
class Group(Rule): 
    """ 
    Pseudo class to group different subrules into one group (mainly to prevent 
    AndRule and OrRule from collecting all subrules in the following example: 
 
    rule1 = Literal('Test') + Literal('value') 
    rule2 = Literal('Test2') + Literal('value2') 
    combine = rule1 + rule2 
 
    In this naive example rule1 would in the end contain all four literals due 
    to the fact that AndRule (which is created by the +) concatenates all subsequent 
    + to one rule. By surrounding both rules (1 and 2) with Group(...) one can 
    prevent this. 
    """ 
    def __init__(self, grouped_rule): 
      self.__grouped_rule = grouped_rule 
      
    def match(self, input_reader): 
      return self.returnToken(self.callAction(self.__grouped_rule.match(input_reader))) 
    
    def __str__(self): 
      return '(' + str(self.__grouped_rule) + ')' 
 
class Literal(Rule):
    """
    Rule matching a certain string. The rule matches a given string. The string
    matches the len(string) next characters, regardless if the input reader
    should ignored whitespaces or not.
    """
    def __init__(self, string):
        """
        Initialize the rule with the string to match.

        @param string: The string this rule instance should match.
        @type  string: str
        """
        self.__string = string

    def __str__(self):
        """
        Return a string representation of this rule.

        @return: a string representation of this rule.
        """
        return "\"%s\"" % self.__string

    def match(self, input_reader):
        """
        Match this rule against the input.

        @param input_reader: The input reader to read the string from.
        @type  input_reader: InputReader
        @return: The matched string.
        """
        input_reader.checkPoint()
        try:
            string = input_reader.getString(len(self.__string))
            if string != self.__string:
                input_reader.rollback()
                raise ParseException("Expected '%s' at position %d. Got '%s'" % (self.__string, input_reader.getPos(), string))
        except EndOfStringException:
            input_reader.rollback()
            raise ParseException("Expected '%s' at end of string" % self.__string)
        input_reader.deleteCheckpoint()
        logging.debug("Matched \"%s\"" % self)
        return self.returnToken(self.callAction([self.__string]))

class AnyOf(Rule):
    """
    A class to match chars from a charset. The class matches exactly one of the chars from
    the given charset. Whitespaces are matched depending on the setting of the input reader.
    Note that if the input reader is set to ignore whitespaces, they will not be matched even
    if the charset contains a whitespace character.
    """
    def __init__(self, set):
        """
        Initialize the object with a given set.

        @param set: the charset this rule should match
        @type  set: str
        """
        self.__set = set

    def __str__(self):
        """
        Return a human readable representation of the rule.

        @return: A string describing the rule
        """
        return "AnyOf(%s)" % self.__set

    def match(self, input_reader):
        """
        Match a character from the input. Depending on the setting of the input reader, the next
        character ist matched directly or the next non-whitespace character is matched.

        @param input_reader: The input to read from.
        @type  input_reader: InputReader
        @return: The matched character
        """
        input_reader.checkPoint()
        char = ''
        try:
            char = input_reader.getChar()
            if not (char in self.__set):
                input_reader.rollback()
                raise ParseException("Expected char from: [%s] at %d" % (self.__set, input_reader.getPos()))
        except EndOfStringException:
            input_reader.rollback()
            raise ParseException("Expected char from: [%s] at %d" % (self.__set, input_reader.getPos()))
        input_reader.deleteCheckpoint()
        logging.debug("Matched %s" % char)
        return self.returnToken(self.callAction([char]))

class NoneOf(Rule):
    """
    Match if the next character is NOT in the given set.
    """
    def __init__(self, set):
        """
        Initialize the rule with the given set.

        @param set: The char set the rule should NOT match on.
        @type  set: str
        """
        self.__set = set
        
    def __str__(self):
        """
        Return a human readable representation of the rule.

        @return A string describing the rule
        """
        return "NoneOf(%s)" % self.__set

    def match(self, input_reader):
        """
        Match the rule against the input.

        @param input_reader: The input reader to read the next character from.
        @type  input_reader: InputReader
        @return: The matched char not in the set.
        """
        input_reader.checkPoint()
        char = ''
        try:
            char = input_reader.getChar()
            if char in self.__set:
                input_reader.rollback()
                raise ParseException("Expected char not from: [%s] at %d" % (self.__set, input_reader.getPos()))
        except EndOfStringException:
            input_reader.rollback()
            raise ParseException("Expected char not from: [%s] at %d" % (self.__set, input_reader.getPos()))
        input_reader.deleteCheckpoint()
        logging.debug("Matched %s" % char)
        return self.returnToken(self.callAction([char]))
    
class AndRule(Rule):
    """
    Two or more rules matching directly after each other.  This rule
    concats two or more subrules matching directly after each other in
    the input.  The class is not to be used directly, but merely is
    created by the +-operator of the Rule class.
    """
    def __init__(self, left_rule, right_rule):
        """
        Create the rule object with two sub-rules.

        @param left_rule: The left subrule of the +-operator creating this object.
        @type  left_rule: Rule
        @param right_rule: The right subrule of the +-operator creating this object.
        @type  right_rule: Rule
        """
        self.__subrules = [left_rule, right_rule]

    def __str__(self):
        """
        Return a human-readable representation of the rule object.

        @return a string describing this rule.
        """
        return "(%s)" % ' '.join(map(str, self.__subrules))

    def __add__(self, right_rule):
        """
        Add another subrule to this object. The +-operator from Rule is overwritten in
        order to concat all subsequent subrules into one single object.

        @param right_rule: The right rule of the +-operator. This object is added as a subrule to self.
        @type  right_rule: Rule
        """
        self.__subrules.append(right_rule)
        return self
    
    def match(self, input_reader):
        """
        Match the input against all subrules. The rule as a whole
        matches if all subrules sucessfully match.

        @param input_reader: The input reader where to read the input from.
        @type  input_reader: InputReader
        @return: A list of token matched by that rule
        """
        retval = []
        try:
            input_reader.checkPoint()
            for rule in self.__subrules:
                result = rule.match(input_reader)
                if result != None:
                    retval.append(result)
            input_reader.deleteCheckpoint()
        except ParseException:
            input_reader.rollback()
            raise
        return self.returnToken(self.callAction(retval))

# TODO: implement a greedy version of the OR rule (matches the longer match of the two)
class OrRule(Rule):
    """
    A set of alternative rules. This object matches one of the
    alternative subrules contained in it. The rules are matched in
    left-to-right order. Matching stops after a rule matches.
    
    This class is not intended for direct use. It is created by the
    |-operator of the Rule class.
    """
    def __init__(self, left_rule, right_rule):
        """
        Initialize this rule with two subrules.

        @param left_rule: The left operand of the creating |-operator.
        @type  left_rule: Rule
        @param right_rule: The right operand of the creating |-operator
        @type  right_rule: Rule
        """
        self.__subrules  = [left_rule, right_rule]

    def __str__(self):
        """
        Return a human readable representation of that rule.

        @return: The string representation of that rule.
        """
        return "(%s)" % ' | '.join(map(str, self.__subrules))

    def __or__(self, right_rule):
        """
        Reimplementation of the |-operator to concat subsequent rules into one
        object. This serves the purpose of simplifying the structure of the
        resulting parser.

        @param right_rule: The right operand of the |-operator.
        @type  right_rule: Rule
        @return: self
        """
        self.__subrules.append(right_rule)
        return self

    def match(self, input_reader):
        """
        Match the subrules of this rule against the input. The matching is done
        in left-to-right order and stops after the first match.

        @param input_reader: The input reader to read characters from.
        @type  input_reader: InputReader
        @return: A list of token matched by the first matching subrule.
        """
        input_reader.checkPoint()
        for rule in self.__subrules:
            try:
                rule_match = rule.match(input_reader)
                input_reader.deleteCheckpoint()
                return self.returnToken(self.callAction(rule_match))
            except ParseException:
                pass
        input_reader.rollback()
        raise ParseException("None of the subrules of %s matched." % str(self))

# TODO: unclear semantic
# class Not(Rule):
#     """Negate the outcome of a rule

#     Note: This does not consume any chars. It merely tells whether
#     the given rule would match at this point
#     """
#     __rule = None
    
#     def __init__(self, rule):
#         self.__rule = rule

#     def __str__(self):
#         return "!%s" % self.__rule

#     def match(self, input_reader):
#         match = False
#         try:
#             input_reader.checkPoint()
#             self.__rule.match(input_reader)
#             input_reader.rollback()
#             match = True
#         except ParseException:
#             input_reader.rollback()
#         if match:
#             input_reader.rollback()
#             raise ParseException("Would not expect rule to match at %d" % input_reader.getPos())
#         input_reader.deleteCheckpoint()
    
class Optional(Rule):
    """
    This rule matches its subrule optionally once. If the subrule does
    not match, the Optional() rule matches anyway.
    """
    def __init__(self, rule):
        """
        Initialize the rule with a subrule.

        @param rule: The rule to match optionally
        @type  rule: Rule
        """
        self.__rule = rule

    def __str__(self):
        """
        Return a string representation of this rule.

        @return: a human readable representation of this rule.
        """
        return "[ %s ]" % str(self.__rule)

    def match(self, input_reader):
        """
        Match this rule against the input.

        @param input_reader: The input reader to read from.
        @type  input_reader: InputReader
        @return A list of token matched by the subrule (or None, if none)
        """
        try:
            rule_match = self.__rule.match(input_reader)
            logging.debug("Matched %s" % self)
            return self.returnToken(self.callAction(rule_match))
        except ParseException:
            pass
            
class OneOrMore(Rule):
    """
    Match a rule once or more. This rule matches its subrule at least
    once or as often as possible.
    """
    def __init__(self, rule):
        """
        Initialize the rule with the appropriate subrule.

        @param rule: The subrule to match.
        @type  rule: Rule
        """
        self.__rule = rule

    def __str__(self):
        """
        Return a human-readable representation of the rule.

        @return: A string describing this rule.
        """
        return "{ %s }1" % str(self.__rule)

    def match(self, input_reader): 
      """ 
      Match the rule against the input. The rule will try to match 
      as many bytes as possible from the input against the 
      subrule. It matches successfully, if the subrule matches at 
      least once. 
  
      @param input_reader: The input reader to read from. 
      @type  input_reader: InputReader 
      @return: A list of token generated by the subrule. 
      """ 
      retval = [] 
      # skip the whitespace here to prevent errors at the end of the string 
      if input_reader.getIgnoreState(): 
        input_reader.skipWhite() 
      retval.append(self.__rule.match(input_reader)) 
      try: 
          while True: 
            if input_reader.getIgnoreState(): 
              input_reader.skipWhite() 
            retval.append(self.__rule.match(input_reader)) 
      except ParseException: 
          pass 
      return self.returnToken(self.callAction(retval))

class Combine(Rule):
    """
    Pseudo rule that recursivly combines all of it's children into one token.
    This rule is useful if the token of a group of subrules should be combined
    to form one string.
    """
    def __init__(self, rule):
        """
        Initialize the rule with a subrule.  The token generated by
        the subrule are recursivly combined into one string.

        @param rule: The subrule to combine.
        @type  rule: Rule
        """
        self.__rule = rule

    def __str__(self):
        """
        Return a human-readable description of the rule.

        @return: A string describing this rule.
        """
        return "Combine(%s)" % str(self.__rule)

    def combine(self, token):
        """
        Recursivly combine all token into a single one. This is an internal helper that
        recursivly combines a list of lists (or strings) into one string.

        @param token: the token list to combine into one string.
        @type  token: list or str
        """
        if token==None:
            return None
        retval = ''
        for tok in token:
            if isinstance(tok, list):
                retval+=self.combine(tok)
            else:
                retval+=tok
        return retval

    def match(self, input_reader):
        """
        Match this rule against the input. The rule matches the input
        against its subrule and combines the resulting token into a
        string.

        @param input_reader: The input reader to read from.
        @type  input_reader: InputReader
        @return: A string combining all the token generated by the subrule.
        """
        retval = self.combine(self.__rule.match(input_reader))
        return self.returnToken(self.callAction(retval))


def Word(param):
    """
    a shortcut for Combine(MatchWhite(OneOrMore(AnyOf(string)))) or
    Combine(MatchWhite(OneOrMore(param))) (depending on the type of
    param). See there for further details.
    """
    if isinstance(param, str):
        return Combine(MatchWhite(OneOrMore(AnyOf(param))))
    else:
        return Combine(MatchWhite(OneOrMore(param)))

class ZeroOrMore(Rule):
    """
    Match a rule ad infinitum. This rule is similar to the Optional()
    rule. While this one only matches if the subrule matches 0 or 1
    times, the ZeroOrMore rule matches at any time. This rule tries to
    consume as much input as possible.
    """
    def __init__(self, rule):
        """
        Initialize this rule with a subrule. The subrule is
        transformed to a Optional(OneOrMore(rule)) construct.

        @param rule: The subrule to match.
        @type  rule: Rule
        """
        self.__rule = Optional(OneOrMore(rule))

    def __str__(self):
        """
        Return a human readable representation of the rule.

        @return A description of this rule.
        """
        return "{ %s }" % str(self.__rule)

    def match(self, input_reader):
        """
        Match the input against the subrule.

        @param input_reader: The input reader to read from.
        @type  input_reader: InputReader
        @return: A list of token generated by the matching of the subrule.
        """
        retval = self.__rule.match(input_reader)
        return self.returnToken(self.callAction(retval))

class IgnoreWhite(Rule):
    """
    A pseudo-rule to tell the parser to temporary ignore
    whitespaces. This rule itself does not match anything. It merely
    sets the input reader into 'ignore whitespace' mode and returns
    the token produced by its subrule. After executing the subrule,
    the ignore state of the input reader is reset (i.e. if it was
    'ignore' before, it will be afterwards, if it was 'match', it will
    be that).
    """
    def __init__(self, rule):
        """
        Initialize the rule with a subrule.

        @param rule: The subrule to match.
        @type  rule: Rule
        """
        self.__rule = rule

    def __str__(self):
        """
        Return a human-readable representation of this rule.

        @return: A string describing this rule.
        """
        return "IgnoreWhite(%s)" % str(self.__rule)

    def match(self, input_reader):
        """
        Match the input against this rule. The input reader is set to
        'ignore whitespace' mode, the subrule is matched, the ignore
        state of the input reader is reset and the result of the
        subrule is returned.

        @param input_reader: The input reader to read any input from.
        @type  input_reader: InputReader
        @return: The results of the subrule.
        """
        ignore = input_reader.getIgnoreState()
        input_reader.setIgnoreState(True)
        try:
            result = self.__rule.match(input_reader)
        except:
            input_reader.setIgnoreState(ignore)
            raise
        input_reader.setIgnoreState(ignore)
        return self.returnToken(self.callAction(result))

class MatchWhite(Rule):
    """
    A pseudo-rule to tell the parser to temporary match
    whitespaces. This rule is the counterpart of the IgnoreWhite
    rule. It sets the input reader into 'match whitespace' mode and
    matches the given subrule.
    """
    def __init__(self, rule):
        """
        Initialize this rule with a subrule.

        @param rule: The rule to match as a subrule.
        @type  rule: Rule
        """
        self.__rule = rule

    def __str__(self):
        """
        Return a human-readable description of the rule.

        @return: A human-readable description of this rule.
        """
        return "MatchWhite(%s)" % str(self.__rule)

    def match(self, input_reader):
        """
        Match this rule against the input. The rule sets the input
        reader into 'match whitespace' mode, matches the subrule,
        resets the ignore state and returns the results of the
        subrule.

        @param input_reader: The input reader to read input from.
        @type  input_reader: InputReader
        @return: A list of token generated by the subrule.
        """
        ignore = input_reader.getIgnoreState()
        input_reader.setIgnoreState(False)
        # skip the trailing whitespace before the subrule matches.
        input_reader.skipWhite()
        try:
            result = self.__rule.match(input_reader)
        except:
            input_reader.setIgnoreState(ignore)
            raise
        input_reader.setIgnoreState(ignore)        
        return self.returnToken(self.callAction(result))

class CallbackParser(Rule):
    """
    A class calling a function for the next input character to
    determine a match.  This class calls a user-supplied function for
    the next input character in order to determine whether the
    character should match or not.
    """
    def __init__(self, callback):
        """
        Initialize the object with a callback. The callback takes a
        single character as parameter and returns True if it should
        match and False otherwise:

        @param callback: The callback function determining the match.
        @type  callback: Callable
        """
        self.__callback = callback

    def __str__(self):
        """
        Return a human-readable description of the rule.

        @return: A human-readable description of this rule.
        """
        return "CallbackParser(%s)" % str(self.__callback.__name__)

    def match(self, input_reader):
        """
        Match this rule against the input. The rule calls the callback
        to determine whether the next character should match or not
        and returns the character if so.

        @param input_reader: The input reader to read input from.
        @type  input_reader: InputReader
        @return: The matched character, if any.
        """
        input_reader.checkPoint()
        try:
            char = input_reader.getChar()
        except EndOfStringException:
            input_reader.rollback()
            raise ParseException('Preliminary end of string')
        if self.__callback(char):
            input_reader.deleteCheckpoint()
            return self.returnToken(self.callAction([char]))
        else:
            input_reader.rollback()
            raise ParseException('Character did not match %s' % str(self))

class ErrorRule(Rule):
    """
    A rule triggering a parse exception. This class is not intended
    to be used directly. Use the predefined variable error instead.
    """
    def __str__(self):
        """
        Return a human-readable description of the rule.

        @return: A human-readable description of this rule.
        """
        return "ErrorRule()"

    def match(self, input_reader):
        """
        Raise a parse exception. Since the only purpose of this rule is
        to raise an exception, this method does not read anything but throws
        an error immediately.
        """
        raise ParseException('Hit ErrorRule()')

alpha    = CallbackParser(lambda char: char.isalpha())
digit    = CallbackParser(lambda char: char.isdigit())
integer  = Word(digit).setAction(lambda i: int(i))
hexdigit = AnyOf('0123456789abcdefABCDEF')
error    = ErrorRule()

def parse(parser, string, ignore_white=True):
    """
    The main parse function. Call this function to parse an input
    string with a given grammar. The parse function will save you from
    setting up the appropriate input reader and parse result.

    @param parser: The entry point to the grammar defined by Rule objects as provided by the framework.
    @type  parser: Rule
    @param string: The input string to parse.
    @type  string: str
    @param ignore_white: The ignore state of the input reader. True if the input reader should ignore whitespaces, False otherwise.
    @type  ignore_white: boolean
    @return: A ParseResult object containing the results of the parsing of the input string.
    """
    input_reader = InputReader(string, ignore_white)
    tokens = parser.match(input_reader)
    return ParseResult(input_reader, tokens)
