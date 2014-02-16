#!/usr/bin/env python

import roller
import sys

if len(sys.argv) > 1:
    root_dir = sys.argv[1]
else:
    root_dir = None

kernel = roller.Kernel(root_dir)
kernel.cleanup()
