# spec: PLS-315 12.4
# description: Non-ASCII identifiers.
# Ported from CPython 3.15.0 Lib/test/test_unicode_identifiers.py (docs/licenses/python.txt);
# library imports are replaced by core equivalents, each change marked "(Ported)".
from harness import *

class PEP3131Test(unittest.TestCase):

    def test_valid(self):
        class T:
            ä = 1
            µ = 2 # this is a compatibility character
            蟒 = 3
            x󠄀 = 4
        self.assertEqual(getattr(T, "\xe4"), 1)
        self.assertEqual(getattr(T, "\u03bc"), 2)
        self.assertEqual(getattr(T, '\u87d2'), 3)
        self.assertEqual(getattr(T, 'x\U000E0100'), 4)

    def test_non_bmp_normalized(self):
        𝔘𝔫𝔦𝔠𝔬𝔡𝔢 = 1
        self.assertIn("Unicode", dir())

    def test_invalid(self):
        try:
            import badsyntax_3131  # noqa: F401 (Ported) from the fixtures directory
        except SyntaxError as err:
            self.assertEqual(str(err),
              "invalid character '€' (U+20AC) (badsyntax_3131.py, line 2)")
            self.assertEqual(err.lineno, 2)
            self.assertEqual(err.offset, 1)
        else:
            self.fail("expected exception didn't occur")

if __name__ == "__main__":
    unittest.main()
