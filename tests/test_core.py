import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hd184_apply as hd

class HolderGate(unittest.TestCase):
    def test_fictional_prefix_is_eligible(self):
        self.assertTrue(hd.is_replaceable('hd_fictional_governor_d_longxi_184'))
    def test_historical_and_empty_are_protected(self):
        for x in (None, '', '0', 'tao_qian', 'my_hd_fictional_1'):
            self.assertFalse(hd.is_replaceable(x), x)

if __name__ == '__main__': unittest.main()
