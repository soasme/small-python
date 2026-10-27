# spec: PLS-315 13.2
# description: A very long list display.
# Ported from CPython 3.15.0 Lib/test/test_longexp.py (docs/licenses/python.txt);
# library imports are replaced by core equivalents, each change marked "(Ported)".
from harness import *

class LongExpText(unittest.TestCase):
    def test_longexp(self):
        REPS = 65580
        l = eval("[" + "2," * REPS + "]")
        self.assertEqual(len(l), REPS)

if __name__ == "__main__":
    unittest.main()
