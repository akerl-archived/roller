roller
=========

[![Latest Version](https://img.shields.io/pypi/v/roller.svg)](https://pypi.python.org/pypi/roller/)
[![Dependency Status](https://img.shields.io/gemnasium/akerl/roller.svg)](https://gemnasium.com/akerl/roller)
[![Build Status](https://img.shields.io/circleci/project/akerl/roller/master.svg)](https://circleci.com/gh/akerl/roller)
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
    * -r, --revision: set new revision to create
    * -c, --config: kernel config file to get the initial configuration from (defaults to current running version)
        * "current", which is the default, will use /proc/config.gz
        * "none" will base configuration on `make allnoconfig` rather than using current or a saved config file
    * -o, --output: Where to save new config, "none" to skip saving
    * -m, --modify: Launch a menuconfig UI to allow customization of the kernel config
    * -s, --skip-install: don't install kernel to /boot
    * -p, --patch: Open a shell before configuration to allow patching the kernel tree
    * -b, --build-dir: Set path to use for downloading/extracting kernel (defaults to /tmp)

## Installation

    pip install roller

## License

roller is released under the MIT License. See the bundled LICENSE file for details.

