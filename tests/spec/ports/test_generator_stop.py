# spec: PLS-315 27.2.1, 14.13
# description: PEP 479: StopIteration escaping a generator becomes RuntimeError, chained as its cause.
# Ported from CPython 3.15.2 Lib/test/test_generator_stop.py (docs/licenses/python.txt);
# library imports are replaced by core equivalents, each change marked "(Ported)".
from __future__ import generator_stop

# (Ported) unittest is the harness's core equivalent.
from harness import *


class TestPEP479(unittest.TestCase):
    def test_stopiteration_wrapping(self):
        def f():
            raise StopIteration
        def g():
            yield f()
        with self.assertRaisesRegex(RuntimeError,
                                    "generator raised StopIteration"):
            next(g())

    def test_stopiteration_wrapping_context(self):
        def f():
            raise StopIteration
        def g():
            yield f()

        try:
            next(g())
        except RuntimeError as exc:
            self.assertIs(type(exc.__cause__), StopIteration)
            self.assertIs(type(exc.__context__), StopIteration)
            self.assertTrue(exc.__suppress_context__)
        else:
            self.fail('__cause__, __context__, or __suppress_context__ '
                      'were not properly set')


if __name__ == '__main__':
    unittest.main()
