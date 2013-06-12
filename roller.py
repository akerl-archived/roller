#!/usr/bin/env python3

VERSION = '0.2.2'

import os
import sys
import shutil
import fileinput
import functools
import urllib.request
import tarfile
import gzip
import subprocess
import multiprocessing
import argparse
import string


def get_args():
    parser = argparse.ArgumentParser(
        description='Simplified kernel rolling tool'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=VERSION
    )
    parser.add_argument(
        '-k', '--kernel',
        dest='new_version',
        default=get_latest_kernel_version(),
        help='Kernel version to build',
    )
    parser.add_argument(
        '-n', '--new-revision',
        dest='new_revision',
        type=str,
        default=None,
        help='Kernel revision to create',
    )
    parser.add_argument(
        '-c', '--config',
        dest='config_version',
        default=get_current_kernel_version(),
        help='Config version to work from',
    )
    parser.add_argument(
        '-r', '--config-revision',
        dest='config_revision',
        type=str,
        default='current',
        help='Config revision to work from',
    )
    parser.add_argument(
        '-s', '--skip-install',
        dest='skip_install',
        action='store_true',
        help='Do not install kernel to /boot'
    )
    return parser.parse_args()


def get_latest_kernel_version(kind='stable'):
    kernel_url = 'https://www.kernel.org/finger_banner'
    search_string = 'The latest {0}'.format(kind)
    with urllib.request.urlopen(kernel_url) as handle:
        for raw_line in handle.readlines():
            line = str(raw_line, encoding='utf8').rstrip('\n')
            if search_string in line:
                return line.rstrip(' (EOL)').rsplit(' ', 1)[1]
    raise LookupError('Could not find the latest {0} kernel'.format(kind))


def get_current_kernel_version():
    return os.uname().release.split('_', 1)[0]


def get_current_kernel_revision():
    current_revision = os.uname().release.rsplit('_', 1)[1]
    if all(x in set(string.digits) for x in current_revision):
        return current_revision
    else:
        return '0'


def require_attr(attribute):
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if getattr(self, attribute, None) is None:
                raise LookupError(
                    'Required attribute is unset: {0}'.format(attribute)
                )
            method(self, *args, **kwargs)
        return wrapper
    return decorator


class Kernel(object):
    def __init__(self, root_dir=None):
        self.version = None
        self.revision = None
        self.config_version = None
        self.config_revision = None

        if root_dir is None:
            if len(sys.argv[0]):
                os.chdir(os.path.dirname(sys.argv[0]))
            self.root_dir = os.getcwd()
        else:
            self.root_dir = os.path.expanduser(root_dir.rstrip('/'))
            os.chdir(self.root_dir)

        for subdir in ['/sources', '/archives', '/configs']:
            os.makedirs(self.root_dir + subdir, 0o755, True)

        raw_configs = [
            x.split('_')
            for x in os.listdir(self.root_dir + '/configs')
            if '_' in x
        ]
        self.existing_configs = {
            x[0]: [] for x in raw_configs
        }
        for config in raw_configs:
            self.existing_configs[config[0]].append((config[1]))

    @require_attr('version')
    def download(self):
        if self.version[0] == '2':
            major = self.version[0:3]
        else:
            major = '3.x'
        if 'rc' in self.version:
            testing = 'testing/'
        else:
            testing = ''

        destination = '{0}/archives/linux-{1}.tar.bz2'.format(
            self.root_dir,
            self.version
        )
        source = 'http://www.kernel.org/pub/linux/kernel/v{0}/{1}linux-{2}.tar.xz'.format(
            major,
            testing,
            self.version
        )

        if os.path.isfile(destination):
            return
        try:
            urllib.request.urlretrieve(source, filename=destination)
        except:
            os.remove(destination)
            raise

    @require_attr('version')
    def extract(self):
        destination = '{0}/sources/'.format(self.root_dir)
        source = '{0}/archives/linux-{1}.tar.bz2'.format(
            self.root_dir,
            self.version
        )

        if os.path.isdir('{0}linux-{1}'.format(destination, self.version)):
            return
        if not os.path.isfile(source):
            raise EnvironmentError('Archived kernel does not exist')
        try:
            archive = tarfile.open(source)
            archive.extractall(destination)
        except:
            shutil.rmtree(
                '{0}linux-{1}'.format(destination, self.version),
                ignore_errors=True
            )
            raise

    @require_attr('version')
    @require_attr('revision')
    @require_attr('config_version')
    @require_attr('config_revision')
    def configure(self, merge_method='oldconfig'):
        os.chdir('{0}/sources/linux-{1}'.format(self.root_dir, self.version))
        try:
            subprocess.call(['make', 'mrproper'], stdout=subprocess.DEVNULL)
        except:
            raise EnvironmentError('Failed to clean your kernel tree')
        if self.config_revision == 'current':
            with gzip.open('/proc/config.gz') as old_config:
                with open('.config', 'wb') as new_config:
                    new_config.write(old_config.read())
        else:
            shutil.copy(
                '{0}/configs/{1}_{2}'.format(
                    self.root_dir,
                    self.config_version,
                    self.config_revision
                ),
                '.config'
            )
        done = False
        for line in fileinput.input('.config', inplace=True):
            if not done and line.find('CONFIG_LOCALVERSION') == 0:
                print('CONFIG_LOCALVERSION="_{0}"'.format(self.revision))
                done = True
            else:
                print(line.rstrip())
        if self.config_version != self.version:
            subprocess.call(['make', merge_method])

    @require_attr('version')
    @require_attr('revision')
    def modify(self):
        os.chdir('{0}/sources/linux-{1}'.format(self.root_dir, self.version))
        subprocess.call(['make', 'menuconfig'])
        shutil.copy(
            '.config',
            '{0}/configs/{1}_{2}'.format(
                self.root_dir,
                self.version,
                self.revision,
            ),
        )

    @require_attr('version')
    def make(self, jobs=None, background=True):
        os.chdir('{0}/sources/linux-{1}'.format(self.root_dir, self.version))
        if background:
            stdout = subprocess.DEVNULL
        else:
            stdout = None
        if jobs is None:
            jobs = str(multiprocessing.cpu_count())
        subprocess.call(['make', '-j' + jobs], stdout=stdout, stderr=stdout)

    @require_attr('version')
    @require_attr('revision')
    def install(self):
        os.chdir('{0}/sources/linux-{1}'.format(self.root_dir, self.version))
        shutil.copy(
            'arch/x86/boot/bzImage',
            '/boot/vmlinuz-{0}_{1}'.format(self.version, self.revision)
        )
        with open('/etc/fstab') as handle:
            device = [
                x.split()[0]
                for x in handle.readlines()
                if 'ext' in x
            ][0]
        try:
            int(device[-1])
        except ValueError:
            hd = '(hd0)'
        else:
            hd = '(hd0,0)'
        grub_config = '''
title {0}_{1}
root {3}
kernel /boot/vmlinuz-{0}_{1} root={2} ro\n'''.format(
            self.version, self.revision, device, hd)
        if not os.path.isdir('/boot/grub'):
            os.makedirs('/boot/grub', 0o755, True)
        if not os.path.isfile('/boot/grub/menu.lst'):
            with open('/boot/grub/menu.lst', 'w') as handle:
                handle.write('timeout 25\ndefault0\n\n#START\n')
        done = False
        for line in fileinput.input('/boot/grub/menu.lst', inplace=True):
            print(line.rstrip())
            if not done and line == '#START\n':
                print(grub_config)
                done = True
        if not done:
            raise EnvironmentError('Failed to update /boot/grub/menu.lst')


def easy_roll():
    kernel = Kernel()
    args = get_args()

    kernel.version = args.new_version
    kernel.config_version = args.config_version
    kernel.config_revision = args.config_revision
    if args.new_revision == 'next':
        if args.new_version in kernel.existing_configs:
            kernel.revision = str(
                int(max(kernel.existing_configs[args.new_version])) + 1
            )
        else:
            kernel.revision = '1'
        modify = True
    elif args.new_revision is None:
        if args.new_version == args.config_version:
            if args.config_revision == 'current':
                kernel.revision = get_current_kernel_revision()
            else:
                kernel.revision = args.config_revision
        else:
            kernel.revision = '0'
        modify = False
    else:
        kernel.revision = args.new_revision
        modify = True

    kernel.download()
    kernel.extract()
    kernel.configure()
    if modify:
        kernel.modify()
    kernel.make()
    if not args.skip_install:
        kernel.install()

if __name__ == '__main__':
    easy_roll()

