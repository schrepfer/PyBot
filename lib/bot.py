#!/usr/bin/env python
#
# Copyright 2011. All Rights Reserved.

"""A generic bot class and helpers."""

__author__ = 'schrepfer'

import fnmatch
import inspect
import logging
import re

from lib import connection
from lib import engine
from lib import events


ANSI_COLOR_PATTERN = re.compile(chr(27) + r'\[[\d;]*m')


class Matcher(object):

  def __init__(self, pattern, priority=0, fallthrough=True):
    """Constructor.

    Args:
      pattern: String
      priority: Integer; Lower priority comes first.
      fallthrough: Boolean; Keep matching after a successful match.
    """
    self._pattern = pattern
    self._priority = priority
    self._fallthrough = fallthrough

  def __cmp__(self, other):
    return cmp(self._priority, other._priority)

  @property
  def priority(self):
    return self._priority

  @property
  def fallthrough(self):
    return self._fallthrough

  @property
  def pattern(self):
    return self._pattern

  def match(self, line):
    return None

class RegExpMatcher(Matcher):

  def match(self, line):
    match = re.match(self._pattern, line)
    if match:
      return (line,) + match.groups()
    return None

class GlobMatcher(Matcher):

  def match(self, line):
    if fnmatch.fnmatch(line, self._pattern):
      return line
    return None

class SimpleMatcher(Matcher):

  def match(self, line):
    if self._pattern == line:
      return line
    return None


def trigger(trigger, matcher=RegExpMatcher, **kwargs):
  def wrapper(function):
    if not hasattr(function, 'matchers'):
      function.matchers = []
    function.matchers.append(matcher(trigger, **kwargs))
    return function
  return wrapper


class Bot(object):

  def __init__(self):
    self._triggers = []
    self._previousLine = ''
    self._engine = engine.Engine()
    self._connection = connection.Connection(self._engine)
    events.registerEvents(self, self._engine)
    self.loadTriggers()

  @property
  def connection(self):
    return self._connection

  @property
  def engine(self):
    return self._engine

  def loadTriggers(self):
    triggers = []
    for name, member in inspect.getmembers(self):
      if not inspect.ismethod(member):
        continue
      if not hasattr(member, 'matchers'):
        continue
      for matcher in member.matchers:
        triggers.append((matcher, member))
    self._triggers = sorted(triggers, key=lambda x: x[0].priority)

  @events.event(events.READ)
  def onRead(self, line):
    line = ANSI_COLOR_PATTERN.sub('', line)
    for matcher, callback in self._triggers:
      match = matcher.match(line)
      if match is None:
        continue
      logging.debug('trigger %s', callback.func_name)
      callback(match)
      if not matcher.fallthrough:
        break
    self._previousLine = line
    return True

  def start(self):
    self.engine.start()
