#!/usr/bin/env python3

import os
import sys 
import roller
import sh

location = __file__.rpartition('/')
if location[1] == '/':
  root = location[0]
else:
  root = '.' 
myKernel = roller.Kernel(root)

if os.path.isdir(root + '/configs/.git'):
  try:
    sh.git.pull(_cwd=root + '/configs')
  except:
    print('configs dir is a git repo but pulling failed')
    sys.exit(1)

if len(sys.argv) > 1:
  myKernel.config = sys.argv[1]
else:
  def crunchVersion(version):
    numbers = [ int(x) for x in version[3:].translate(str.maketrans('-rc_.','     ')).split() ]
    if 'rc' in version:
      crunched = 1000
    elif '.' not in version:
      crunched = 0
    else: 
      crunched = -1000
    base = 
    for number in reversed(numbers):
      crunched -= number * base
      base *= 10
    return crunched
    
  versions = [ x for x in sorted(os.listdir(root + '/configs'), reverse=True) if x != '.git' ]
  myKernel.config = [ x for x in sorted(versions, key=crunchVersion) if x[0:3] == versions[0][0:3] ][0]

myKernel.version = myKernel.config.split('_')[0]

if myKernel.getKernel() and myKernel.configure(modify=False) and myKernel.make():
  if myKernel.install(doInstall=True):
    sys.exit(0)
  else:
    sys.exit(1)
else:
  sys.exit(1)

