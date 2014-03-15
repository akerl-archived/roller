import unittest
import roller


class TestRoller:
    def test_easyroll(self):
        roller.easy_roll(['-s', '-v'])
