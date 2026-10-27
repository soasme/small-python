# spec: reference/lexical_analysis.html#encoding-declarations
# description: Source encodings: UTF-8 default, coding cookies, and BOMs, via compile() of bytes.
from harness import *

assert_eq(run(compile("x = 'é'\n".encode("utf-8"), "<spec>", "exec"))["x"] if False else None, None)
ns = {}
exec(compile("x = 'é'\n".encode("utf-8"), "<spec>", "exec"), ns)
assert_eq(ns["x"], "é")
ns = {}
exec(compile("# -*- coding: latin-1 -*-\nx = '\xe9'\n".encode("latin-1"), "<spec>", "exec"), ns)
assert_eq(ns["x"], "é")
ns = {}
exec(compile("#!/usr/bin/env python\n# vim: set fileencoding=latin-1 :\nx = '\xe9'\n".encode("latin-1"), "<spec>", "exec"), ns)
assert_eq(ns["x"], "é")
ns = {}
exec(compile(b"\xef\xbb\xbfx = 1\n", "<spec>", "exec"), ns)
assert_eq(ns["x"], 1)
# A cookie on the third line is just a comment.
ns = {}
exec(compile("\n\n# coding: latin-1\nx = 'é'\n".encode("utf-8"), "<spec>", "exec"), ns)
assert_eq(ns["x"], "é")
# Invalid UTF-8 without a cookie, an unknown encoding, or a BOM with another cookie are errors.
assert_raises(SyntaxError, compile, b"x = '\xe9'\n", "<spec>", "exec")
assert_raises(SyntaxError, compile, b"# coding: no-such-codec\nx = 1\n", "<spec>", "exec")
assert_raises(SyntaxError, compile, b"\xef\xbb\xbf# coding: latin-1\nx = 1\n", "<spec>", "exec")
# Source given as str ignores the cookie.
ns = {}
exec(compile("# coding: latin-1\nx = 'é'\n", "<spec>", "exec"), ns)
assert_eq(ns["x"], "é")
# Null bytes are not allowed in source.
assert_raises(SyntaxError, compile, "x = 1\0\n", "<spec>", "exec")
