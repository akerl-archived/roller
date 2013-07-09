roller
=========

Roller provides a pythonic Kernel object for configuring and compiling kernels, and a streamlined command line tool for using that object

## Usage

    ./roller.py

### Options

    * -v, --verbose: increase verbosity, which includes using progress bars for downloading/extracting
    * -k, --kernel: pick the version you want to build. Defaults to latest stable
    * -n, --new-revision: set new revision to create
        * "next" will automatically increment to the next revision
        * Omit this to build directly from the selected config without modification
    * -c, --config: kernel version to get the initial configuration from. Defaults to current running version
    * -r, --config-revision: kernel revision to use for initial configuration. Defaults to "current", which uses /proc/config.gz
    * -s, --skip-install: don't install kernel to /boot

## Installation

    git clone git://github.com/akerl/roller

## License

roller is released under the MIT License. See the bundled LICENSE file for details.

