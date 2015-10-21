roller
=========

[![Latest Version](https://img.shields.io/pypi/v/roller.svg)](https://pypi.python.org/pypi/roller/)
[![Build Status](https://img.shields.io/circleci/project/akerl/roller.svg)](https://circleci.com/gh/akerl/roller)
[![Coverage Status](https://img.shields.io/codecov/c/github/akerl/roller.svg)](https://codecov.io/github/akerl/roller)
[![Code Quality](https://img.shields.io/codacy/b324f431700a4d41a70f5b7cf23c625f.svg)](https://www.codacy.com/app/akerl/roller)
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
    * -c, --config: kernel version to get the initial configuration from (defaults to current running version)
    * -r, --config-revision: kernel revision to use for initial configuration
        * "current", which is the default, will use /proc/config.gz
        * "none" will base configuration on `make allnoconfig` rather than using current or a saved config file
    * -s, --skip-install: don't install kernel to /boot
    * -p, --patch: Open a shell before configuration to allow patching the kernel tree
    * -b, --build-dir: Set path to use for downloading/extracting kernel (defaults to /tmp)
    * -d, --config-dir: Set path for kernel configs (defaults to $build_dir/configs)

## Installation

    pip install roller

## License

roller is released under the MIT License. See the bundled LICENSE file for details.

