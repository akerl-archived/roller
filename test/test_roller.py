import unittest
import nose
import roller


class TestRoller:
    def test_defaults(self):
        defaults = roller.get_args([])
        assert defaults.verbose is False
        assert defaults.new_version == roller.get_latest_kernel_version()
        assert defaults.revision == 'dev'
        assert defaults.config == 'current'
        assert defaults.output == 'new'
        assert defaults.modify is False
        assert defaults.skip_install is False
        assert defaults.build_dir == '/tmp'

    @nose.tools.raises(SystemExit)
    def test_version(self):
        assert roller.get_args(['--version'])

    def test_arguments(self):
        assert roller.get_args(['-v']).verbose is True
        assert roller.get_args(['-k', '1.2.3']).new_version == '1.2.3'
        assert roller.get_args(['-c', '1.2.3']).config == '1.2.3'
        assert roller.get_args(['-s']).skip_install is True
        assert roller.get_args(['-b', '/foo']).build_dir == '/foo'

    def test_get_latest_kernel_version(self):
        stable = roller.get_latest_kernel_version(kind='stable')
        longterm = roller.get_latest_kernel_version(kind='longterm')
        mainline = roller.get_latest_kernel_version(kind='mainline')
        assert stable != longterm
        assert 'rc' in mainline

    def test_easyroll(self):
        arg_sets = []
        for args in arg_sets:
            roller.easy_roll(args)

    def test_cleanup(self):
        kernel = roller.Kernel()
        kernel.cleanup()
