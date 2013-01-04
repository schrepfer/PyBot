#!/usr/bin/env python
#
# Copyright 2011. All Rights Reserved.

"""A generic bot class and helpers."""

__author__ = 'schrepfer'

import fnmatch
import inspect
import logging
import re
import sre_constants

import connection
import engine
import events


ANSI_COLOR_PATTERN = re.compile(chr(27) + r'\[[\d;]*m')


class Matcher(object):

  def __init__(self, pattern, priority=0, fallthrough=True, raw=False):
    """Constructor.

    Args:
      pattern: String
      priority: Integer; Lower priority comes first.
      fallthrough: Boolean; Keep matching after a successful match.
      raw: Boolean; This matcher should use the raw output.
    """
    self._pattern = pattern
    self._priority = priority
    self._fallthrough = fallthrough
    self._raw = raw

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

  @property
  def raw(self):
    return self._raw

  def match(self, line):
    return None


class RegExpMatcher(Matcher):

  def match(self, line):
    try:
      match = re.search(self._pattern, line)
    except sre_constants.error:
      return None
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
    self._previousLineRaw = ''
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
    stripped = ANSI_COLOR_PATTERN.sub('', line)
    for matcher, callback in self._triggers:
      if matcher.raw:
        match = matcher.match(line)
      else:
        match = matcher.match(stripped)
      if match is None:
        continue
      logging.debug('trigger %s', callback.func_name)
      callback(match)
      if not matcher.fallthrough:
        break
    self._previousLine = stripped
    self._previousLineRaw = line
    return True

  def start(self):
    self.engine.start()
