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
    license='MIT License',
    py_modules=['roller'],
    scripts=['roller.py'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Operating System Kernels :: Linux',
    ],
)
