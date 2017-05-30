#!/usr/bin/env python3
from __future__ import print_function

import os
import sys
import glob
import shutil
import fileinput
import functools
import tarfile
import gzip
import subprocess
import multiprocessing
import argparse
import string
import time
from contextlib import closing

try:
    from urllib.request import urlopen, urlretrieve
except ImportError:
    from urllib2 import urlopen
    from urllib import urlretrieve

VERSION = '1.1.0'

try:
    width = shutil.get_terminal_size((40, 0)).columns
except AttributeError:
    width = 40


def get_args(raw_args):
    parser = argparse.ArgumentParser(
        description='Simplified kernel rolling tool'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=VERSION
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Increase verbosity of output'
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
    parser.add_argument(
        '-p', '--patch',
        dest='patches',
        action='append',
        help='Open a shell before configuration to allow patching'
    )
    parser.add_argument(
        '-b', '--build-dir',
        dest='build_dir',
        type=str,
        default='/tmp',
        help='directory for downloading, extracting, and building the kernel'
    )
    parser.add_argument(
        '-d', '--config-dir',
        dest='config_dir',
        type=str,
        default=None,
        help='directory for kernel configs'
    )
    return parser.parse_args(raw_args)


def get_latest_kernel_version(kind='stable'):
    kernel_url = 'https://www.kernel.org/finger_banner'
    search_string = 'The latest {0}'.format(kind)
    with closing(urlopen(kernel_url)) as handle:
        for raw_line in handle.readlines():
            line = raw_line.decode('utf-8').rstrip('\n')
            if search_string in line:
                return str(line.rstrip(' (EOL)').rsplit(' ', 1)[1])
    raise LookupError('Could not find the latest {0} kernel'.format(kind))


def get_current_kernel_version():
    return os.uname()[2].split('_', 1)[0]


def get_current_kernel_revision():
    current_kernel = os.uname()[2].rsplit('_', 1)
    if len(current_kernel) < 2:
        return '0'
    current_revision = current_kernel[1]
    if all(x in set(string.digits) for x in current_revision):
        return current_revision
    else:
        return '0'


def run_patches(kernel, patches):
    for patch in patches:
        if os.path.isdir(patch):
            run_patches(kernel, glob.glob('{0}/*'.format(patch)))
        elif os.access(patch, os.X_OK):
            kernel.patch(patch)


def devnull():
    return open(os.devnull, 'w')


def progress_bar(current, goal):
    marker_width = width - 7
    percent = round(current / goal, 2)
    mark_count = int(round(marker_width * percent))
    text_bar = '{0:3}% [{1}{2}]'.format(
        int(percent * 100),
        '*' * mark_count,
        ' ' * (marker_width - mark_count),
    )
    try:
        print('\r' + text_bar, end='')
    except:
        sys.stdout.flush()


def download_progress(current_block, block_size, total_size):
    if current_block % 5 == 0:
        current_size = min(current_block * block_size, total_size)
        progress_bar(current_size, total_size)


def extract_progress(extracted_count, total_count):
    if extracted_count % 50 == 0:
        progress_bar(extracted_count, total_count)


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


class TarFileWithProgress(tarfile.TarFile):
    def __init__(self, *args, **kwargs):
        self.callback = kwargs.pop('callback', None)
        super(TarFileWithProgress, self).__init__(*args, **kwargs)
        if self.callback is not None:
            self._total_count = len(self.getmembers())
            self._extracted_count = 0

    def extract(self, *args, **kwargs):
        if self.callback is not None:
            self.callback(self._extracted_count, self._total_count)
            self._extracted_count = self._extracted_count + 1
        super(TarFileWithProgress, self).extract(*args, **kwargs)


class Kernel(object):
    def __init__(self, build_dir=None, config_dir=None, verbose=True):
        self.version = None
        self.revision = None
        self.config_version = None
        self.config_revision = None
        self.verbose = verbose

        if build_dir is None:
            self.build_dir = os.path.dirname(sys.argv[0])
        else:
            self.build_dir = os.path.expanduser(build_dir.rstrip('/'))
        self.build_dir = os.path.abspath(self.build_dir)

        if config_dir is None:
            self.config_dir = self.build_dir + '/configs'
        else:
            self.config_dir = os.path.expanduser(config_dir.rstrip('/'))
        self.config_dir = os.path.abspath(self.config_dir)
        if not os.path.isdir(self.config_dir):
            os.makedirs(self.config_dir, 0o755)

        for subdir in ['/sources', '/archives']:
            if not os.path.isdir(self.build_dir + subdir):
                os.makedirs(self.build_dir + subdir, 0o755)

        raw_configs = [
            x.split('_')
            for x in os.listdir(self.config_dir)
            if '_' in x
        ]
        self.existing_configs = {
            x[0]: [] for x in raw_configs
        }
        for config in raw_configs:
            self.existing_configs[config[0]].append((config[1]))

    def log(self, message):
        if self.verbose:
            print(message)

    @require_attr('version')
    def download(self):
        if 'rc' in self.version:
            base_url = 'https://git.kernel.org/torvalds/t'
            url = '{0}/linux-{1}.tar.xz'.format(base_url, self.version)
        else:
            base_url = 'https://cdn.kernel.org/pub/linux/kernel'
            major = 'v' + self.version[0] + '.x'
            url = '{0}/{1}/linux-{3}.tar.gz'.format(
                base_url,
                major,
                self.version
            )

        destination = '{0}/archives/linux-{1}.tar.gz'.format(
            self.build_dir,
            self.version
        )

        if os.path.isfile(destination):
            self.log('Kernel already downloaded: {0}'.format(self.version))
            return
        self.log('Downloading kernel: {0}'.format(self.version))
        if self.verbose:
            hook = download_progress
        else:
            hook = None
        try:
            urlretrieve(
                url,
                filename=destination,
                reporthook=hook
            )
        except:
            os.remove(destination)
            raise

    @require_attr('version')
    def extract(self):
        destination = '{0}/sources/'.format(self.build_dir)
        source = '{0}/archives/linux-{1}.tar.gz'.format(
            self.build_dir,
            self.version
        )

        if os.path.isdir('{0}linux-{1}'.format(destination, self.version)):
            self.log('Kernel already extracted')
            return
        if not os.path.isfile(source):
            raise EnvironmentError('Archived kernel does not exist')
        self.log('Extracting kernel')
        if self.verbose:
            callback = extract_progress
        else:
            callback = None
        try:
            archive = TarFileWithProgress.open(source, callback=callback)
            archive.extractall(destination)
        except:
            shutil.rmtree(
                '{0}linux-{1}'.format(destination, self.version),
                ignore_errors=True
            )
            raise

    @require_attr('version')
    def patch(self, patch_script):
        os.chdir('{0}/sources/linux-{1}'.format(self.build_dir, self.version))
        self.log('Applying patch: {0}'.format(patch_script))
        if self.verbose:
            output = None
        else:
            output = subprocess.DEVNULL
        resp = subprocess.call([patch_script], stdout=output, stderr=output)
        if resp != 0:
            raise EnvironmentError('Command failed: {0}'.format(patch_script))

    @require_attr('version')
    @require_attr('revision')
    @require_attr('config_version')
    @require_attr('config_revision')
    def configure(self, merge_method='oldconfig'):
        os.chdir('{0}/sources/linux-{1}'.format(self.build_dir, self.version))
        self.log('Cleaning your kernel tree')
        try:
            subprocess.call(['make', 'mrproper'], stdout=devnull())
        except:
            raise EnvironmentError('Failed to clean your kernel tree')
        if self.config_revision == 'none':
            self.log('Using allnoconfig for initial configuration')
            subprocess.call(['make', 'allnoconfig'])
            return
        elif self.config_revision == 'current':
            self.log('Inserting config from current system kernel')
            with gzip.open('/proc/config.gz') as old_config:
                with open('.config', 'wb') as new_config:
                    new_config.write(old_config.read())
        else:
            self.log('Copying saved config: {0}_{1}'.format(
                self.config_version,
                self.config_revision,
            ))
            shutil.copy(
                '{0}/{1}_{2}'.format(
                    self.config_dir,
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
            self.log('Merging your kernel config via "{0}"'.format(
                merge_method)
            )
            subprocess.call(['make', merge_method])

    @require_attr('version')
    @require_attr('revision')
    def modify(self):
        os.chdir('{0}/sources/linux-{1}'.format(self.build_dir, self.version))
        self.log('Running menuconfig')
        subprocess.call(['make', 'menuconfig'])
        self.log('Saving configuration: {0}_{1}'.format(
            self.version,
            self.revision
        ))
        shutil.copy(
            '.config',
            '{0}/{1}_{2}'.format(
                self.config_dir,
                self.version,
                self.revision,
            ),
        )

    @require_attr('version')
    def make(self, jobs=None):
        os.chdir('{0}/sources/linux-{1}'.format(self.build_dir, self.version))
        cap = len(open('.config').readlines())
        if jobs is None:
            jobs = str(multiprocessing.cpu_count())
        self.log('Making the kernel')
        make_process = subprocess.Popen(
            ['make', '-j' + jobs],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        counter = 0
        while len(make_process.stdout.readline()):
            if self.verbose:
                counter += 1
                progress_bar(min(counter, cap), cap)
            make_process.stdout.flush()
        while make_process.poll() is None:
            time.sleep(1)
        if make_process.returncode != 0:
            print('Failed to make kernel')
            raise SystemExit

    @require_attr('version')
    @require_attr('revision')
    def install(self):
        os.chdir('{0}/sources/linux-{1}'.format(self.build_dir, self.version))
        self.log('Installing the kernel image')
        if not os.path.isdir('/boot'):
            os.makedirs('/boot', 0o755)
        shutil.copy(
            'arch/x86/boot/bzImage',
            '/boot/vmlinuz-{0}_{1}'.format(self.version, self.revision)
        )
        try:
            with open('/etc/fstab') as handle:
                device = [
                    x.split()[0]
                    for x in handle.readlines()
                    if 'ext' in x
                ][0]
        except IndexError:
            device = '/dev/xvda'
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
            self.log('Making /boot/grub')
            os.makedirs('/boot/grub', 0o755)
        if not os.path.isfile('/boot/grub/menu.lst'):
            self.log('Creating initial menu.lst')
            with open('/boot/grub/menu.lst', 'w') as handle:
                handle.write('timeout 25\ndefault 0\n\n#START\n')
        self.log('Inserting new kernel into menu.lst')
        done = False
        for line in fileinput.input('/boot/grub/menu.lst', inplace=True):
            print(line.rstrip())
            if not done and line == '#START\n':
                print(grub_config)
                done = True
        if not done:
            raise EnvironmentError('Failed to update /boot/grub/menu.lst')

    def where(self):
        print('{0}/sources/linux-{1}/arch/x86/boot/bzImage'.format(
            self.build_dir, self.version
        ))

    def cleanup(self):
        self.log('Cleaning old archives and sources')
        for archive in os.listdir(self.build_dir + '/archives'):
            os.remove(self.build_dir + '/archives/' + archive)
        for source in os.listdir(self.build_dir + '/sources'):
            shutil.rmtree(self.build_dir + '/sources/' + source)


def easy_roll(raw_args):
    args = get_args(raw_args)
    kernel = Kernel(
        build_dir=args.build_dir,
        config_dir=args.config_dir,
        verbose=args.verbose
    )

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
    if args.patches:
        run_patches(kernel, args.patches)
    kernel.configure()
    if modify:
        kernel.modify()
    kernel.make()
    if args.skip_install:
        kernel.where()
    else:
        kernel.install()

if __name__ == '__main__':
    easy_roll(sys.argv[1:])
