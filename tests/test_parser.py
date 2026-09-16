import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hd184_apply as hd

class ScriptParser(unittest.TestCase):
    def test_nested_braces_quotes_comments_and_bom(self):
        text = '\ufeff# header {\nd_a = { # }\n 184.1.1 = { holder = "hd_fictional_a" effect = { text = "a\\\"}#b" } }\n}'
        nodes = hd.parse_script(text)
        self.assertEqual(nodes[0].key, 'd_a')
        date = nodes[0].children[0]
        self.assertEqual(hd.one(date, 'holder').value, 'hd_fictional_a')
        self.assertEqual(text[date.start:date.end], '184.1.1 = { holder = "hd_fictional_a" effect = { text = "a\\\"}#b" } }')
    def test_typed_color_and_arrays(self):
        n = hd.parse_script('x = { color = hsv { 0.1 0.2 0.3 } laws = { a b } }')[0]
        self.assertEqual(hd.one(n, 'color').prefix, 'hsv')
        self.assertEqual([v.value for v in hd.one(n, 'laws').children], ['a','b'])
    def test_rejects_unbalanced_quote_and_braces(self):
        for s in ('x={', 'x={ a="bad }', 'x={ a=1 }}', 'x='):
            with self.subTest(s=s), self.assertRaises(hd.InputError): hd.parse_script(s)
    def test_normalizes_only_explicit_chinese_variants_and_zero_width(self):
        self.assertEqual(hd.norm('李敏\u200c'), '李敏')
        self.assertEqual(hd.norm('吳幹'), '吴干')
        self.assertEqual(hd.place_name('太山郡'), '泰山')
        self.assertNotEqual(hd.norm('李相如'), hd.norm('李参'))

if __name__ == '__main__': unittest.main()
