#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages


def read(fname):
    buf = open(os.path.join(os.path.dirname(__file__), fname), 'rb').read()
    return buf.decode('utf8')


setup(name='hts-miniterm',
      version='0.1.dev1',
      description='miniterm.py + .hts file parsing',
      long_description=read('README.rst'),
      author='Marc Brinkmann',
      author_email='git@marcbrinkmann.de',
      url='https://github.com/mbr/hts-miniterm',
      license='MIT',
      packages=find_packages(exclude=['tests']),
      install_requires=['click'],
      entry_points={
          'console_scripts': [
              'hts-miniterm = hts_miniterm.cli:cli',
          ],
      },
      classifiers=[
          'Programming Language :: Python :: 3',
      ])
