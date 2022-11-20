# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import collections
import os
import random
import re
import string
import sys
import unittest


_envRegEx = re.compile("\{\$(.*?)\}")
_evalRegEx = re.compile("\{.*?\}")

def _findEnvironmentVariable(matchobj):
  """ 
  Callback from regex substitution which looks up the environment variable named in the matched text.
  Throws an exception if the variable doesn't exist.
  """
  name = matchobj.group(0)[2:-1]
  value = os.getenv(name)
  if value:
    return value
  else:
    raise Exception("Invalid environment variable specified: %s" % name)

def _resolveEnvironmentVariables(value):
  """ Find patterns of the form '{$variable}' and replace with the environment value, returning the result. """
  return re.sub(_envRegEx, _findEnvironmentVariable, value)

class ResolveTable:
  """Used to store name/value pairs that can be resolved in strings.
  Example: Assuming the resolve table has an item "{filename}" that resolves to example.mov,
  Then calling resolveTable.resolve(taskObject, "someprefix_{filename}") will return "someprefix_example.mov"
  To use, create an object, call addResolver on it with whatever key/value pairs you want, and then you can call resolve on the object to resolve a string.
  You can also merge two ResolveTable objects, replacing existing key's with those in the ResolveTable passed in.
  And you can use functions to do the resolve. These take one parameter, the task that the resolve is applying to.
  For an example of how to use this, see FnExporterBase.py.
  """
  
  class StringItem:
    def __init__(self, name, description, value=None):
      self._name = name
      self._description = description
      self._value = value

    def resolve(self, task):
      return str(self._value)
    
    def name(self):
      return self._name
    
    def description(self):
      return self._description
  
  class CallbackItem:
    def __init__(self, name, description, resolver):
      self._name = name
      self._description = description
      self._resolver = resolver

    def resolve(self, task):
      return self._resolver(self._name, task)
    
    def name(self):
      return self._name
    
    def description(self):
      return self._description

  def __init__(self):
    self._resolvers = {}

  def duplicate (self):
    resolveTable = ResolveTable()
    resolveTable._resolvers = dict(self. _resolvers)
    return resolveTable
    
  def entries(self):
    return list(self._resolvers.keys())
  
  def entryCount(self):
    '''self.entryCount() -> returns the number of entries in this resolver.'''
    return len(list(self._resolvers.keys()))
  
  def entryName(self, index):
    '''self.entryCount(index) -> returns the name of the entry based on the index.'''
    return list(self._resolvers.keys())[index]
  
  def entryDescription(self, index):
    '''self.entryDescription(index) -> returns a description of the item, which can be used to populate a dialog to the user when they are picking keywords.'''
    return self._resolvers[self.entryName(index)].description()
    
  def addResolver(self, name, description, resolver):
    if isinstance(resolver, collections.Callable):
      self._resolvers[name] = ResolveTable.CallbackItem(name, description, resolver)
    else:
      self._resolvers[name] = ResolveTable.StringItem(name, description, resolver)

  def merge(self, resolver):
    if (resolver != None):
      self._resolvers.update(resolver._resolvers)

  def pathSensitiveReplace(self, initialString, findValue, replaceValue, isPath):
    if not isPath:
      return initialString.replace(findValue, replaceValue)
    else:
      # find each occurance of the findValue, look for surrounding path elements
      # and be careful to avoid the gotchas of os.path.join
      cursor = 0
      # find the next occurance of string and replace, in a loop
      workingString = initialString

      # TODO - better than while True
      while True:
        cursor = workingString.find(findValue, cursor) # find the next occurance

        if (cursor == -1):
            break

        preceedingIndex = cursor - 1
        nextIndex = cursor + len(findValue)

        pathJoinStart = False
        pathJoinEnd = False

        # break up the working string around the value to replace
        prefix = workingString[:cursor]
        suffix = workingString[nextIndex:]

        # work out if we need to do path joining at the start or end of the substitution
        if (preceedingIndex >= 0):
          pathJoinStart = (prefix.endswith('/'))
        if (nextIndex < len(workingString)):
          pathJoinEnd = (suffix.startswith('/'))
          # we must not lead with a slash if we use path joining - os.path.join will assume it is an
          # absolute path and discard anything it is joined with as a suffix
          if pathJoinEnd:
            suffix = suffix[1:]
        if (replaceValue.startswith("/")):
          pathJoinStart = True
          # we must not lead with a slash if we use path joining - os.path.join will assume it is an
          # absolute path and discard anything it is joined with as a suffix - however not if the
          # preceding bit of string is empty, i.e. if cursor hasn't moved from the start, since we
          # want to use an absolute path in that case actually...
          if cursor != 0:
            replaceValue = replaceValue[1:]
        if (replaceValue.endswith("/")):
          pathJoinEnd = True

        if pathJoinStart:
          workingString = os.path.join(prefix, replaceValue)
        else:
          workingString = prefix + replaceValue

        # SE - NOTE: no idea why this is problematic, but optimisation is not important...
        #cursor = len(workingString)

        if (pathJoinEnd != False):
          workingString = os.path.join(workingString, suffix)
        else:
          workingString = workingString + suffix

      return workingString

  def resolve(self, task, value, isPath=False):
  
    errors = []
    
    value = _resolveEnvironmentVariables(value)
    
    # Build a dictionary of ({token} : resolvedvalue) pairs
    # Can't optimise this by limited contained tokens (as previously) because tokens may resolve to more tokens.
    resolved = dict([(name, resolver.resolve(task)) for name, resolver in self._resolvers.items() ])
    
    # Any {tokens} which match directly, just do a simple replace
    for (resolverName, resolvedValue) in resolved.items():
      if resolvedValue is not None:
        value = self.pathSensitiveReplace(value, resolverName, resolvedValue, isPath)
   
    # Rebuild the dictionary with the {} stripped from the tokens
    # These tokens form the local variables in the eval call
    resolved = dict([(name.strip('{}'), resolvedValue) for name, resolvedValue in resolved.items()])
    
    # Find and iterate over all instances of "\{.*?\}"
    for expression in _evalRegEx.findall(value):
      try:
        # Try and evaluate the expression within the {}, passing the dictionary of tokens as local variables
        resolvedExpression = eval(expression.strip('{}'), resolved)
        
        # If the expression does not return a valid value, raise and exception
        if resolvedExpression is None:
          raise Exception("Expression did not evaluate to a value")
          
        # Replace the expression in the string with the result of the eval
        value = self.pathSensitiveReplace(value, expression, str(resolvedExpression), isPath)
        
      except Exception as error:
        # Collate all errors so can be reported together
        errors.append("Evaluation of '%s' failed with the error:\n%s" % (expression, str(error)))
    
    # If error raise exception with collated error strings
    if len(errors) > 0:
      raise RuntimeError("\n\n".join(errors))
    
    return value
  
  def addEntriesToExportStructureViewer(self, viewer):
    for (name, entry) in self._resolvers.items():
      viewer.setResolveEntry(name, "", entry.description())


# SE - unit tests - these are here to aid in unit test discovery

testTokens = [["foo", "foo"], ["bar", "bar"], ["foobar", "foobar"], ["x", "expanded"]]
testPathyTokens = [["foo", "/foo"], ["bar", "bar/"], ["foobar", "/foobar/"], ["x", "expanded"]]

class ResolveTableTests(unittest.TestCase):
  def createSimpleResolveTable(self):
    resolver = ResolveTable()
    for tokenData in testTokens:
      resolver.addResolver("{" + tokenData[0] + "}", "some description", lambda keyword, task: tokenData[1])
    return resolver

  def createPathyResolveTable(self):
    resolver = ResolveTable()
    for tokenData in testPathyTokens:
      resolver.addResolver("{" + tokenData[0] + "}", "some description", lambda keyword, task: tokenData[1])
    return resolver

  def randomLowercaseString(self, length):
    return ''.join(random.choice(string.lowercase) for i in range(length))

  def testEmptyString(self):
    """ Make sure we don't fall over on the empty string. """

    resolver = self.createSimpleResolveTable()

    testCase = ""

    self.assertEqual(testCase, resolver.resolve(None, testCase, isPath=False))
    self.assertEqual(testCase, resolver.resolve(None, testCase, isPath=True))

  def testNoTokens(self):
    """ Make sure we don't fall over if there are no tokens to resolve. """

    resolver = self.createSimpleResolveTable()

    # pick some kinda random strings not containing { or }
    # and try resolving the things in it...
    for i in range(0, 1000):
      testCase = self.randomLowercaseString(random.randrange(1,1000))

      self.assertEqual(testCase, resolver.resolve(None, testCase, isPath=False))
      self.assertEqual(testCase, resolver.resolve(None, testCase, isPath=True))

  def testBadTokenInString(self):
    """ Make sure we throw an exception if the string contains a single unexpected token. """

    resolver = self.createSimpleResolveTable()

    for i in range(0, 1000):
      testCase = self.randomLowercaseString(random.randrange(4,10))

      if (testCase != "foobar"): # the other strings in the resolver are too short.
        prefix = "" # try to catch edge cases where the string starts or ends with token
        suffix = ""

        if random.randrange(0,10) > 3:
          prefix = self.randomLowercaseString(random.randrange(4,10))
        if random.randrange(0,10) > 3:
          suffix = self.randomLowercaseString(random.randrange(4,10))

        testCase = prefix + "===---{" + testCase + "}---===" + suffix

        self.assertRaises(RuntimeError, resolver.resolve, None, testCase, isPath=False)
        self.assertRaises(RuntimeError, resolver.resolve, None, testCase, isPath=True)

  def testBadTokensInString(self):
    """ Make sure we throw an exception if the string contains multiple unexpected tokens. """

    resolver = self.createSimpleResolveTable()

    for i in range(0, 1000):
      testCase = ""

      for j in range(0, random.randrange(2,10)):
        prefix = "" # try to catch edge cases where the string starts or ends with token
        suffix = ""

        if random.randrange(0,10) > 3:
          prefix = self.randomLowercaseString(random.randrange(4,10))

        if random.randrange(0,10) > 3:
          suffix = self.randomLowercaseString(random.randrange(4,10))

        badToken = self.randomLowercaseString(random.randrange(7,10)) # avoid foobar
        testCase = testCase + prefix + "===---{" + badToken + "}---===" + suffix

      self.assertRaises(RuntimeError, resolver.resolve, None, testCase, isPath=False)
      self.assertRaises(RuntimeError, resolver.resolve, None, testCase, isPath=True)

  def testGoodTokenInString(self):
    """ Make sure we get the expected result when substituting a single token. """

    resolver = self.createSimpleResolveTable()

    for i in range(0,100):
      for tokenData in testTokens:
        prefix = "" # try to catch edge cases where the string starts or ends with token
        suffix = ""

        if random.randrange(0,10) > 3:
          prefix = self.randomLowercaseString(random.randrange(4,10))
        if random.randrange(0,10) > 3:
          suffix = self.randomLowercaseString(random.randrange(4,10))

        testCase = prefix + "{" + tokenData[0] + "}" + suffix
        expectedResult = prefix + tokenData[1] + suffix

        self.assertEqual(expectedResult, resolver.resolve(None, testCase, isPath=False))
        self.assertEqual(expectedResult, resolver.resolve(None, testCase, isPath=True))

  def testGoodTokensInString(self):
    """ Make sure we get the expected result when substituting multiple tokens. """

    resolver = self.createSimpleResolveTable()

    for i in range(0, 1000):
      testCase = ""
      expectedResult = ""

      for j in range(3,20):
        tokenData = random.choice(testTokens)
        prefix = "" # try to catch edge cases where the string starts or ends with token
        suffix = ""

        if random.randrange(0,10) > 3:
          prefix = self.randomLowercaseString(random.randrange(4,10))
        if random.randrange(0,10) > 3:
          suffix = self.randomLowercaseString(random.randrange(4,10))

        testCase = testCase + prefix + "{" + tokenData[0] + "}" + suffix
        expectedResult = expectedResult + prefix + tokenData[1] + suffix

      self.assertEqual(expectedResult, resolver.resolve(None, testCase, isPath=False))
      self.assertEqual(expectedResult, resolver.resolve(None, testCase, isPath=True))

  def testTP155479(self):
    """ Check that when isPath=True paths are normalised and don't have repeated /'s. """

    resolver = self.createPathyResolveTable()

    for i in range(0, 1000):
      testCase = ""
      expectedResult = ""

      for j in range(3,20):
        tokenData = random.choice(testTokens)

        prefix = "" # try to catch edge cases where the string starts or ends with token or /
        suffix = ""

        if random.randrange(0,10) > 5:
          prefix = "/"
        if random.randrange(0,10) > 3:
          prefix = prefix + self.randomLowercaseString(random.randrange(4,10))
        if random.randrange(0,10) > 3:
          suffix = self.randomLowercaseString(random.randrange(4,10))

        testCase = testCase + prefix + "{" + tokenData[0] + "}" + suffix

      resolvedString = resolver.resolve(None, testCase, isPath=True)
      self.assertEqual("//" in resolvedString, False)
