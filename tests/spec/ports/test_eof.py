"""test script for a few new invalid token catches"""

# spec: PLS-315 11.2, 12.2.2, 12.5.1, 18.2.2
# description: CPython's test_eof: unterminated string literals and a line continuation at the end of input, from str, bytes, BOM and declared-encoding sources.
# Ported from CPython 3.15.2 Lib/test/test_eof.py (docs/licenses/python.txt);
# library imports are replaced by core equivalents, each change marked "(Ported)".
from harness import *
# (Ported) unittest is the harness's core equivalent. The tests that run a
# script in a subprocess check the command-line host's error display and are
# omitted.
BOM_UTF8 = b"\xef\xbb\xbf"  # (Ported) codecs.BOM_UTF8

class EOFTestCase(unittest.TestCase):
    def test_EOF_single_quote(self):
        expect = "unterminated string literal (detected at line 1) (<string>, line 1)"
        for quote in ("'", "\""):
            with self.assertRaises(SyntaxError) as cm:
                eval(f"""{quote}this is a test\
                """)
            self.assertEqual(str(cm.exception), expect)
            self.assertEqual(cm.exception.offset, 1)

    def test_EOFS(self):
        expect = ("unterminated triple-quoted string literal (detected at line 3) (<string>, line 1)")
        with self.assertRaises(SyntaxError) as cm:
            eval("""ä = '''thîs is \na \ntest""")
        self.assertEqual(str(cm.exception), expect)
        self.assertEqual(cm.exception.text, "ä = '''thîs is ")
        self.assertEqual(cm.exception.offset, 5)

        with self.assertRaises(SyntaxError) as cm:
            eval("""ä = '''thîs is \na \ntest""".encode())
        self.assertEqual(str(cm.exception), expect)
        self.assertEqual(cm.exception.text, "ä = '''thîs is ")
        self.assertEqual(cm.exception.offset, 5)

        with self.assertRaises(SyntaxError) as cm:
            eval(BOM_UTF8 + """ä = '''thîs is \na \ntest""".encode())
        self.assertEqual(str(cm.exception), expect)
        self.assertEqual(cm.exception.text, "ä = '''thîs is ")
        self.assertEqual(cm.exception.offset, 5)

        with self.assertRaises(SyntaxError) as cm:
            eval("""# coding: latin1\nä = '''thîs is \na \ntest""".encode('latin1'))
        self.assertEqual(str(cm.exception), "unterminated triple-quoted string literal (detected at line 4) (<string>, line 2)")
        self.assertEqual(cm.exception.text, "ä = '''thîs is ")
        self.assertEqual(cm.exception.offset, 5)

    def test_eof_with_line_continuation(self):
        expect = "unexpected EOF while parsing (<string>, line 1)"
        # (Ported) host.warnings records the SyntaxWarning the decorator ignored.
        def thunk():
            with self.assertRaises(SyntaxError) as cm:
                compile('"\\Xhh" \\', '<string>', 'exec')
            self.assertEqual(str(cm.exception), expect)
        host.warnings(thunk)

    def test_line_continuation_EOF(self):
        """A continuation at the end of input must be an error; bpo2180."""
        expect = 'unexpected EOF while parsing (<string>, line 1)'
        with self.assertRaises(SyntaxError) as cm:
            exec('ä = 5\\')
        self.assertEqual(str(cm.exception), expect)
        self.assertEqual(cm.exception.text, 'ä = 5\\\n')
        self.assertEqual(cm.exception.offset, 7)

        with self.assertRaises(SyntaxError) as cm:
            exec('ä = 5\\'.encode())
        self.assertEqual(str(cm.exception), expect)
        self.assertEqual(cm.exception.text, 'ä = 5\\\n')
        self.assertEqual(cm.exception.offset, 7)

        with self.assertRaises(SyntaxError) as cm:
            exec('# coding:latin1\nä = 5\\'.encode('latin1'))
        self.assertEqual(str(cm.exception),
                         'unexpected EOF while parsing (<string>, line 2)')
        self.assertEqual(cm.exception.text, 'ä = 5\\\n')
        self.assertEqual(cm.exception.offset, 7)

        with self.assertRaises(SyntaxError) as cm:
            exec(BOM_UTF8 + 'ä = 5\\'.encode())
        self.assertEqual(str(cm.exception), expect)
        self.assertEqual(cm.exception.text, 'ä = 5\\\n')
        self.assertEqual(cm.exception.offset, 7)

        with self.assertRaises(SyntaxError) as cm:
            exec('\\')
        self.assertEqual(str(cm.exception), expect)



if __name__ == "__main__":
    unittest.main()


if __name__ == "__main__":
    unittest.main()
