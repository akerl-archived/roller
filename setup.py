#!/usr/bin/env python3

from distutils.core import setup

setup(name='roller',
      version='0.1.2',
      description='Kernel rolling helper',
      author='Les Aker',
      author_email='me@lesaker.org',
      url= 'https://github.com/akerl/roller',
      py_modules= ['roller'],
      requires= ['sh'],
     )

