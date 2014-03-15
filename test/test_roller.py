import unittest
import nose
import roller


class TestRoller:
    def test_defaults(self):
        defaults = roller.get_args([])
        assert defaults.verbose is False
        assert defaults.new_version == roller.get_latest_kernel_version()
        assert defaults.new_revision is None
        assert defaults.config_version == roller.get_current_kernel_version()
        assert defaults.config_revision == 'current'
        assert defaults.skip_install is False
        assert defaults.build_dir == '/tmp'
        assert defaults.config_dir is None

    @nose.tools.raises(SystemExit)
    def test_version(self):
        assert roller.get_args(['--version'])

    def test_arguments(self):
        assert roller.get_args(['-v']).verbose is True
        assert roller.get_args(['-k', '1.2.3']).new_version == '1.2.3'
        assert roller.get_args(['-n', '9']).new_revision == '9'
        assert roller.get_args(['-c', '1.2.3']).config_version == '1.2.3'
        assert roller.get_args(['-r', '7']).config_revision == '7'
        assert roller.get_args(['-s']).skip_install is True
        assert roller.get_args(['-b', '/foo']).build_dir == '/foo'
        assert roller.get_args(['-d', '/bar']).config_dir == '/bar'

    def test_get_latest_kernel_version(self):
        stable = roller.get_latest_kernel_version(kind='stable')
        longterm = roller.get_latest_kernel_version(kind='longterm')
        mainline = roller.get_latest_kernel_version(kind='mainline')
        assert stable != longterm
        assert 'rc' in mainline

    def test_get_current_kernel_version(self):
        assert len(roller.get_current_kernel_version().split('.')) > 1

    def test_get_current_kernel_revision(self):
        assert roller.get_current_kernel_revision() == '0'

    def test_easyroll(self):
        arg_sets = [
            ['-v', '-k', '3.13.6', '-c', '3.13.6', '-r', '1']
        ]
        for args in arg_sets:
            roller.easy_roll(args)

    def test_cleanup(self):
        kernel = roller.Kernel()
        kernel.cleanup()
