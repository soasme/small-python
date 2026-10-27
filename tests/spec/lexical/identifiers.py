# spec: PLS-315 12.4
# description: Identifier characters, NFKC normalization, keywords, soft keywords, reserved names.
from harness import *

ns = run("_ = 1\n__ = 2\na1 = 3\n_a_b_ = 4\nÄpfel = 5\nπ = 6\n変数 = 7\n")
assert_eq(ns["Äpfel"], 5)
assert_eq(ns["変数"], 7)
assert_syntax_error("1a = 1\n")
assert_syntax_error("a$ = 1\n")
assert_syntax_error("€ = 1\n")

# Identifiers are NFKC-normalized while parsing: ﬁ (U+FB01) is fi, ℌ is H.
ns = run("ﬁle = 1\nℌ = 2\n")
assert_eq(ns["file"], 1)
assert_eq(ns["H"], 2)
assert_true("ﬁle" not in ns)
assert_eq(run("x = 1\nｘ = 2\n")["x"], 2)  # fullwidth x normalizes to x
# Keywords are matched as spelled, so ｉｆ is the name if; a name that
# normalizes to None, True, or False cannot be compiled, wherever it is.
assert_eq(run("ｉｆ = 1\n")["if"], 1)
for source in ["Ｔrue = 1\n", "x.Ｎone\n", "def f(Ｆalse): pass\n", "Ｔrue = 1\n)\n"]:
    assert_raises(ValueError, compile, source, "<s>", "exec")
assert_syntax_error(")\nＴrue = 1\n")

# Hard keywords cannot be used as identifiers.
for word in ["False", "None", "True", "and", "as", "assert", "async", "await", "break", "class",
             "continue", "def", "del", "elif", "else", "except", "finally", "for", "from", "global",
             "if", "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise",
             "return", "try", "while", "with", "yield"]:
    assert_syntax_error(f"{word} = 1\n")
    assert_true(word.isidentifier())

# Soft keywords are ordinary names outside their statements.
ns = run("match = 1\ncase = 2\ntype = 3\n_ = 4\nlazy = 5\nmatch += case\n")
assert_eq((ns["match"], ns["case"], ns["type"], ns["lazy"]), (3, 2, 3, 5))
ns = run("def match(case): return case\nx = match(5)\nclass type: pass\n")
assert_eq(ns["x"], 5)

# Names that differ only in case are distinct.
ns = run("a = 1\nA = 2\n")
assert_eq((ns["a"], ns["A"]), (1, 2))

# str.isidentifier follows the same rules.
assert_true("_private".isidentifier())
assert_true("Ünïcödé".isidentifier())
assert_false("9lives".isidentifier())
assert_false("".isidentifier())
assert_false("a-b".isidentifier())

# Private names are mangled inside a class body (see expressions/names).
class Spam:
    __secret = 1
    def get(self):
        return self.__secret
assert_eq(Spam().get(), 1)
assert_true(hasattr(Spam, "_Spam__secret"))
assert_false(hasattr(Spam, "__secret"))
