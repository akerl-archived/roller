#!/usr/bin/env python

import os
import sys
import shutil
import fileinput

try:
  import sh
except:
  print("It looks like you don't have the sh module installed.")
  sys.exit(1)

def extract(version):
  try:
    print('Extracting kernel from archive')
    To = '{0}sources/'.format(myHome)
    From = '{0}archives/linux-{1}.tar.bz2'.format(myHome,version)
    show = feedback('About to untar, should it be run in the foreground? [y/N]', bool, 'no', '? ')  
    sh.tar('-x', '-v', C = To, f = From, _fg=show)
  except:
    print('Failed to extract predownloaded archive archive')
    print('Cleaning up any orphans from extraction')
    shutil.rmtree('{0}linux-{1}'.format(To,choice),ignore_errors=True)
    return False
  return True

def download(version):
  if version[0] == '2':
    major = version[0:3]
  else:
    major = '3.x'
  if version.find('rc') != -1:
    testing ='testing/'
  else:
    testing = ''
  To = '{0}archives/linux-{1}.tar.bz2'.format(myHome,version)
  From = 'http://www.kernel.org/pub/linux/kernel/v{0}/{1}linux-{2}.tar.bz2'\
    .format(major,testing,version)
  print('Trying to pull kernel from {0}'.format(From))
  try:
    show = feedback('About to wget, should it be run in the foreground? [y/N]', bool, 'no', '? ')
    sh.wget(From, O = To, _fg=show)
  except:
    print('Failed to download kernel')
    print('Cleaning up any orphaned bits')
    os.remove(To)
    return False
  return True

def getSource(version):
  if version in mySources:
    return True
  elif version in myArchives:
    if extract(version):
      return True
  elif len(version) and not len(version.strip('01234567890.-rc')): 
    if download(version) and extract(version):
      return True
  return False

def feedback(message = None, validate = None, default = None, inputMsg = '? [{0}] '):
  if message is not None:
    print(message)
  while True:
    tmp = input(inputMsg.format(default))
    if tmp == '' and default is not None:
      tmp = default
    tmp = tmp.lower()
    if validate is bool:
      if tmp in ['y','yes']:
        return True
      elif tmp in ['n','no']:
        return False
    elif validate is int:
      if tmp.isdigit():
        return int(tmp)
    elif type(validate) is list:
      if type(validate[0]) is tuple:
        for item in validate:
          if tmp in item:
            return item[0]
      elif tmp in validate:
        return tmp
    elif hasattr(validate, '__call__'):
      if validate(tmp):
        return tmp

def configMenu(version):
  options = [('current','c')]
  prompt = '''What config do you want to use?
    [c]urrent (use the currently running kernel's config)'''
  if version in myConfigs:
    for revision in myConfigs[version]:
      options.append(('{0}_{1}'.format(version,revision), revision))
      prompt+='''    
    {0}_[{1}]'''.format(version,revision)
  for key in sorted(myConfigs.keys(), reverse=True):
    if key == version:
      continue
    options.append((key))
    options.append(tuple( '{0}_{1}'.format(key,x) for x in myConfigs[key] ))
    prompt+=''''
    [{0}] ({1} config(s))'''.format(key,len(myConfigs[key]))
  choice = feedback(prompt, options, 'current')
  if choice == 'current' or choice.find('_'):
    return choice
  configMenu(choice)

myHome=__file__.rstrip('role.py')
for dir in ['sources','archives','configs']:
  os.makedirs(myHome + dir, 0o755, True)

myArchives = [ x[6:-8] for x in os.listdir(myHome + 'archives') ]
mySources = [ x[6:] for x in os.listdir(myHome + 'sources') ]
mySources.sort(key = lambda source: source.replace('-rc','.'), reverse = True)
myDefault = ''
for source in mySources:
  myDefault = source
  if source.find('rc') == -1:
    break
raw_configs = [ ( x.split('_')[0], x.split('_')[1] ) 
  for x in os.listdir('configs/') if len(x.partition('_')[2]) ]
myConfigs = { x[0] : [] for x in raw_configs }
for config in raw_configs:
  myConfigs[config[0]].append((config[1]))

prompt = '''What kernel version do you want to use?'''
if len(mySources):
  prompt +='''
  Currently unpacked kernels:'''
  for source in mySources:
    prompt += '''
    {0}'''.format(source)
if len(myArchives) and not myArchives <= mySources:
  prompt +='''
  Currently downloaded archives (unpacked sources not listed):'''
  for archive in myArchives:
    if archive not in mySources:
      prompt +='''
    {0}'''.format(archive)
myVersion = feedback(prompt, getSource, myDefault)
myConfig = configMenu(myVersion)

try:
  os.chdir('{0}sources/linux-{1}'.format(myHome,myVersion))
except:
  print('Failed to switch into kernel source')
  sys.exit(1)

if os.path.isfile('.config'):
  if not feedback('Your kernel source has a .config file. Do you want to clean it? [y/N]', bool, 'no', '? '):
    sys.exit()
print('Cleaning your kernel tree')
try:
  sh.make('mrproper')
except:
  print('Failed to make mrproper your kernel source!')
  sys.exit(1)

if myConfig == 'current':
  prompt = '''Which merge method would you like to use?
    [o]ldconfig
    local[m]odconfig
    local[y]esconfig'''
  options = [ ('oldconfig','old','o'),
              ('localmodconfig','mod','m'),
              ('localyesconfig','yes','y')]
  cmd = feedback(prompt, options, 'mod')
  try:
    sh.make(cmd, _fg=True)
  except:
    print('Failed to make {0} your kernel source!'.format(cmd))
    sys.exit(1)
else:
  shutil.copy('../../configs/' + myConfig,'./.config')

if myVersion in myConfigs:
  myRevision = str(len(myConfigs[myVersion])+1)
else:
  myRevision = 1

try:
  for line in fileinput.input('.config',inplace=True):
    if line[0:19] == 'CONFIG_LOCALVERSION':
      print('CONFIG_LOCALVERSION="_{0}"'.format(myRevision))
    else:
      print(line.rstrip())
except:
  print('Failed to prepare .config with new version')
  sys.exit(1)

input('Press enter to work some menuconfig magic!')
sh.make('menuconfig', _fg=True)

if feedback('Should configuration {0}_{1} be saved? [Y/n]'.format(myVersion,myRevision), bool, 'yes', '? '):
  shutil.copy('./.config','../../configs/{0}_{1}'.format(myVersion,myRevision))

show = feedback('Run make in foreground? [Y/n]', bool, 'yes', '? ')

try:
  sh.make( j=4, _fg=show)
except:
  print('Failed to make your kernel!')
  sys.exit(1)

if feedback('Install kernel to /boot/? [y/N]', bool, 'no', '? '):
  try:
    shutil.copy('arch/x86/boot/bzImage', '/boot/vmlinuz-{0}_{1}'.format(myVersion,myRevision))
  except:
    print('Failed to put /boot/vmlinuz-{0}_{1} into place'.format(myVersion,myRevision))
  try:
    handle = open('/boot/grub/menu.lst')
    hd, dev = None, None
    for line in handle:
      if line[0:4] == 'root':
        hd = line.split()[1]
      elif line[0:6] == 'kernel':
        for item in line.split():
          if item[0:4] == 'root':
            dev = item[5:]
      if hd is not None and dev is not None:
        break
    handle.close()
    check = True
    for line in fileinput.input('/boot/grub/menu.lst',inplace=True):
      if line == '\n' and check:
        print('''
title {0}_{1}
root {2}
kernel /boot/vmlinuz-{0}_{1} root={3} ro
'''.format(myVersion, myRevision, hd, dev))
        check = False
      else:
        print(line.rstrip())
  except:
    print('Failed to modify /boot/grub/menu.lst')

if feedback('Proactively clean the kernel source? [Y/n]', bool, 'yes', '? '):
  sh.make('mrproper')

print('Victory!')

