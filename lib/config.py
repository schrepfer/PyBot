#!/usr/bin/env python
#
# Copyright 2011. All Rights Reserved.

"""Common config related functions."""

__author__ = 'schrepfer'

import ConfigParser
import os


def readConfig(config_file, config_format=None):
  if config_format is None:
    config_format = {
      'character': ['name', 'password'],
      'server': ['address', 'port'],
      }

  assert os.path.isfile(config_file), 'Missing config file: %s' % config_file

  config = ConfigParser.ConfigParser()
  config.read(config_file)

  for section, options in config_format.iteritems():
    assert config.has_section(section), 'Missing section: %s' % section
    for option in options:
      assert config.has_option(section, option), 'Missing option: %s > %s' % (section, option)
      assert config.get(section, option), 'Must not be blank: %s > %s' % (section, option)

  return config


