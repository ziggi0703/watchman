#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import

import click
import sys
import logging

from watchman import __version__

__author__ = "Michael Ziegler"
__copyright__ = "Michael Ziegler"
__license__ = "none"

_logger = logging.getLogger(__name__)


@click.command()
@click.option('--config', '-c', type=str, help='path to config file')
def cli(config):
    click.echo('Run watchman')
    click.echo('Load config: {}'.format(config))
