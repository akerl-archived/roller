#!/usr/bin/env python3

import roller

from distutils.core import setup

setup(
    name='roller',
    version=roller.VERSION,
    description='Kernel rolling helper',
    author='Les Aker',
    author_email='me@lesaker.org',
    url='https://github.com/akerl/roller',
    py_modules=['roller'],
    scripts=['roller.py'],
)
