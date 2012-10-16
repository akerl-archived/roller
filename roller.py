#!/usr/bin/env python

import os
import sys
import shutil
import fileinput
import sh

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

class Kernel(object):
  def __init__(self, root, version = None, config = None, repo = None):
    self.root = os.path.expanduser(root)
    self.version = version
    self.config = config
    self.repo = repo
    self.gotten = False
    self.error = False
    self.errormsg = None
    self.progressCount = 0

    for dir in ['sources','archives','configs']:
      os.makedirs(self.root + dir, 0o755, True)

    self.Archives = [ x[6:-8] for x in os.listdir(myHome + 'archives') ]
    self.Sources = [ x[6:] for x in os.listdir(myHome + 'sources') ]
    self.Sources.sort(key = lambda source: source.replace('-rc','.'), reverse = True)
    self.DefaultConfig = ''
    for source in self.Sources:
      self.Default = source
      if source.find('rc') == -1: 
        break
    raw_configs = [ ( x.split('_')[0], x.split('_')[1] ) 
      for x in os.listdir('configs/') if len(x.partition('_')[2]) ]
    self.Configs = { x[0] : [] for x in raw_configs }
    for config in raw_configs:
      self.Configs[config[0]].append((config[1]))

  def caught(self, msg = None):
    if msg is None:
      print('Caught due to previous error: {0}'.format(self.errormsg))
    else:
      print(msg)
      self.error = True
      self.errormsg = msg

  def progressDots(line, stdin, proc):
    if self.progressCount > 5:
      print('.', end = None)
      self.progressCount = 0
    self.progressCount += 1

  def download(self, version = None):
    if version is None and self.version is None:
      self.caught('Cannot download with no version set')
      return False
    if version is None:
      version = self.version


    if version[0] == '2':
      major = version[0:3]
    else:
      major = '3.x'
    if version.find('rc') != -1:
      testing = 'testing/'
    else:
      testing = ''

    destination = '{0}/archives/linux-{1}.tar.bz2'.format(self.root,version)
    source = 'http://www.kernel.org/pub/linux/kernel/v{0}/{1}linux-{2}.tar.bz2'.format(major,testing,version)

    if os.path.isfile(destination):
      return True

    if not self.quiet: print('Pulling kernel from {0}'.format(source))
    try:
      sh.wget(source, O=destination)
    except:
      os.remove(destination)
      return False
    return True

  def extract(self, version = None):
    if version is None and self.version is None:
      self.caught('Cannot extract with no version set')
      return False
    if version is None:
      version = self.version

    destination = '{0}/sources/'.format(self.root)
    source = '{0}archives/linux-{1}.tar.bz2'.format(self.root,version)

    if os.path.isdir('{0}linux-{1}'.format(destination,version)):
      return True

    try:
      sh.tar(x=True, C=destination, f=source)
    except:
      shutil.rmtree('{0}linux-{1}'.format(destination,version), ignore_errors=True)
      return False
    return True

  def getKernel(self, version = None):
    if version is None and self.version is None:
      self.caught('Cannot get kernel with no version set')
      return False
    if version is None:
      version = self.version

    if len(version) and not len(version.strip('01234567890.-rc')): 
      if download(version) and extract(version):
        self.gotten = True
        return True
    return False

  def configMenu(self, version):
    options = [('current','c')]
    prompt = '''What config do you want to use?
  [c]urrent (use the currently running kernel's config)'''

    if version in self.Configs:
      for revision in self.Configs[version]:
        options.append(('{0}_{1}'.format(version,revision), revision))
        prompt+='''    
  {0}_[{1}]'''.format(version,revision)

    for key in sorted(self.Configs.keys(), reverse=True):
      if key == version:
        continue
      options.append((key))
      options.append(tuple( '{0}_{1}'.format(key,x) for x in self.Configs[key] ))
      prompt+=''''
  [{0}] ({1} config(s))'''.format(key,len(self.Configs[key]))

    choice = feedback(prompt, options, 'current')
    if choice == 'current' or choice.find('_'):
      return choice
    self.configMenu(choice)

  def get(self):
    prompt = '''What kernel version do you want to use?'''
    if len(self.Sources):
      prompt +='''
  Currently unpacked kernels:'''
      for source in self.Sources:
        prompt += ''' 
    {0}'''.format(source)
    if len(self.Archives) and not myArchives <= mySources:
      prompt +='''
  Currently downloaded archives (unpacked sources not listed):'''
      for archive in myArchives:
        if archive not in mySources:
          prompt +='''
    {0}'''.format(archive)

    self.version = feedback(prompt, self.getKernel, self.Default)
    self.config = self.configMenu(self.Version)
    return True

  def configure(self, merge = None, modify = True):
    if self.error:
      self.caught()
      return False
    if self.version is None and self.config is None:
      self.caught('Cannot configure without a version or config set')
      return False
    if not self.gotten:
      self.caught('Cannot configure without getting the kernel')
      return False

    try:
      os.chdir('{0}/sources/linux-{1}'.format(self.root,self.version))
    except:
      self.caught('Failed to chdir into kernel directory')
      return False

    try:
      sh.make.mrproper()
    except:
      self.caught('Failed to make mrproper your tree')
      return False

    try:
      if self.config == 'current':
        sh.zcat('/proc/config.gz', _out='.config')
      else:
        shutil.copy('../../configs/{0}'.format(self.config), '.config')
    except:
      self.caught('Failed to load your config')
      return False

    if merge is None:
      prompt = '''Which merge method would you like to use?
  [o]ldconfig
  local[m]odconfig
  local[y]esconfig'''
      options = [ ('oldconfig','old','o'), ('localmodconfig','mod','m'), ('localyesconfig','yes','y')]
      merge = feedback(prompt, options, 'mod')

    try:
      sh.make(merge)
    except:
      self.caught('Failed to make {0} your kernel source!'.format(merge))
      return False

    if modify is True:
      if self.version in self.Configs:
        self.revision = str(len(self.Configs[self.version])+1)
      else:
        self.revision = 1
      try:
        for line in fileinput.input('.config', inplace=True):
          if line[0:19] == 'CONFIG_LOCALVERSION':
            print('CONFIG_LOCALVERSION="_{0}"'.format(self.revision))
          else:
            print(line.rstrip())
      except:
        self.caught('Failed to prepare .config with new revision')
        return False
      try:
        os.system('make menuconfig')
      except:
        self.caught('Failed to make menuconfig')
        return False

      shutil.copy('.config', '../../configs/{0}_{1}'.format(self.version, self.revision))

      if os.path.isdir('../../configs/.git'):
        sh.git.commit(_cwd=self.root + '/configs',
          a=True, m='Added {0}_{1}'.format(self.version, self.revision))
        try:
          sh.git.push(_cwd=self.root + '/configs')
        except:
          pass
    else:
      self.revision = self.config.rsplit('_',1)[-1]        

    print('Making the kernel')
    try:
      sh.make(j=4, _out=self.progressDots)
    except:
      self.caught('Failed to make your kernel')
      return False
    return True

  def install(self, doInstall = None):
    if self.error:
      self.caught()
      return False

    if doInstall is None:
      doInstall = feedback('Install kernel to /boot/? [y/N]', bool, 'no', '? '):
    if doInstall is False:
      return False

    try:
      shutil.copy('arch/x86/boot/bzImage', '/boot/vmlinuz-{0}_{1}'.format(self.version,self.revision))
    except:
      self.caught('Failed to copy vmlinuz into place')
      return False

    try:
      with open('/proc/partitions') as handle:
        dev = None
        for line in handle:
          tmp = line.rsplit(None,1)
          if len(tmp) and tmp[1] != 'name':
            dev = '/dev/' + tmp[1]
            break
      if dev == '/dev/xvda':
        hd = '(hd0)'
      else:
        hd = '(hd0,0)'

      grubConfig = '''
title {0}_{1}
root {2}
kernel /boot/vmlinuz-{0}_{1} root={3} ro
'''.format(self.version, self.revision, hd, dev)

      if not os.path.isdir('/boot/grub'):
        os.makedirs('/boot/grub', 0o755, True)
      if not os.path.isfile('/boot/grub/menu.lst'):
        with open('/boot/grub/menu.lst', 'w') as handle:
          handle.write('''timeout 25
default 0
''' + grubConfig)
      else:
        edited = False
        for line in fileinput.input('/boot/grub/menu.lst')
          if edited is False and line = '\n':
            print(grubConfig)
            edited = True
          else:
            print(line.rstrip())
    except:
      self.caught('Failed to edit grub config')
      return False

    return True

  def simple(self):
    if self.get() and self.configure() and self.make(): self.install()


if __name__ == "__main__":
  location = __file__.rpartition('/')
  if location[1] == '/':
    root = location[0]
  else:
    root = '.'
  myKernel = Kernel(root)
  myKernel.simple()

