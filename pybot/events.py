#!/usr/bin/env python
#
# Copyright 2011. All Rights Reserved.

"""Events which are registered and triggered."""

__author__ = 'schrepfer'

import inspect
import logging
import Queue

def event(event, priority=0):
  def wrapper(function):
    if not hasattr(function, 'events'):
      function.events = []
    function.events.append((event, priority))
    return function
  return wrapper


def registerEvents(inst, engine):
  for name, member in inspect.getmembers(inst):
    if not inspect.ismethod(member):
      continue
    if not hasattr(member, 'events'):
      continue
    for e, p in member.events:
      engine.eventManager.register(e, member, priority=p)


class Event(object):

  def __init__(self, key, description):
    self._key = key
    self._description = description

  @property
  def key(self):
    return self._key

  @property
  def description(self):
    return self._description

  def __str__(self):
    return '%s (%s)' % (self._description, self._key)


class EventManager(object):

  def __init__(self, engine):
    self._queue = Queue.Queue()
    self._events = {}
    self._engine = engine

  def triggerEvent(self, event, *args, **kwargs):
    if not isinstance(event, Event):
      return
    logging.debug('!%s %r %r', event.key, args, kwargs)
    self._queue.put((event, args, kwargs))
    return True

  def register(self, event, callback, priority=0):
    if not isinstance(event, Event):
      return
    callbacks = self._events.setdefault(event, [])
    position = 0
    for f, p in callbacks:
      if priority < p:
        break
      position += 1
    logging.debug('register %s %s (%d)', event.key, callback, priority)
    callbacks.insert(position, (callback, priority))

  def eventDispatcher(self):
    while self._engine.running():
      event, args, kwargs = self._queue.get()
      for callback, priority in self._events.get(event, []):
        try:
          if not callback(*args, **kwargs):
            break
        except Exception, e:
          logging.error('%s: %s', e.__class__.__name__, e)
          break


BELL = Event('BELL', 'Audible/Visual Bell')
CONFAIL = Event('CONFAIL', 'Connection failure')
CONNECT = Event('CONNECT', 'Connected to the server')
DISCONNECT = Event('DISCONNECT', 'Disconnected from server')
INPUT = Event('INPUT', 'Input read from stdin')
READ = Event('READ', 'Read from the socket')
SEND = Event('SEND', 'Send to the socket')
SHUTDOWN = Event('SHUTDOWN', 'Shutdown')
STARTUP = Event('STARTUP', 'Startup')
TICK = Event('TICK', 'Heartbeat')
