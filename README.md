roller
=========

[![Latest Version](https://img.shields.io/pypi/v/roller.svg)](https://pypi.python.org/pypi/roller/)
[![Coverage Status](https://img.shields.io/coveralls/akerl/roller.svg)](https://coveralls.io/r/akerl/roller)
[![Build Status](https://img.shields.io/travis/akerl/roller.svg)](https://travis-ci.org/akerl/roller)
[![MIT Licensed](https://img.shields.io/badge/license-MIT-green.svg)](https://tldrlegal.com/license/mit-license)

Roller provides a pythonic Kernel object for configuring and compiling kernels, and a streamlined command line tool for using that object

## Usage

    ./roller.py

### Options
    * -h, --help: show the help text
    * --version: show the version
    * -v, --verbose: increase verbosity, which includes using progress bars for downloading/extracting
    * -k, --kernel: pick the version you want to build. (defaults to latest stable)
    * -n, --new-revision: set new revision to create
        * "next" will automatically increment to the next revision
        * Omit this to build directly from the selected config without modification
    * -c, --config: kernel version to get the initial configuration from. (defaults to current running version)
    * -r, --config-revision: kernel revision to use for initial configuration. (defaults to "current", which uses /proc/config.gz)
    * -s, --skip-install: don't install kernel to /boot
    * -p, --patch: Open a shell before configuration to allow patching the kernel tree
    * -b, --build-dir: Set path to use for downloading/extracting kernel (defaults to /tmp)
    * -d, --config-dir: Set path for kernel configs (defaults to $build_dir/configs)

## Installation

    pip install roller

## License

roller is released under the MIT License. See the bundled LICENSE file for details.

