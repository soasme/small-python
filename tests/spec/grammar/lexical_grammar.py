# spec: PLS-315 A.1, 12.4.2, 12.6
# description: The lexical grammar of Annex A: identifiers, keywords, string prefixes, and number literals.
from harness import *

# Keywords cannot be names; soft keywords can.
keywords = ("False None True and as assert async await break class continue def del elif else "
            "except finally for from global if import in is lambda nonlocal not or pass raise "
            "return try while with yield").split()
for word in keywords:
    assert_syntax_error(f"{word} = 1\n")
for word in ("match", "case", "_", "type", "lazy"):
    assert_eq(run(f"{word} = 1\n")[word], 1)

# identifier: id_start id_continue*
for name in ("_", "_x9", "é", "x\u0300", "ℕ", "Ω"):
    assert_compiles(f"{name} = 1\n")
for bad in ("9x", "x$", "\u0300x", "x€"):
    assert_syntax_error(f"{bad} = 1\n")

# stringprefix, any letter uppercase; u combines with nothing.
for prefix in ("r", "u", "b", "br", "rb", "f", "fr", "rf", "t", "tr", "rt",
               "R", "U", "B", "bR", "Rb", "F", "fR", "Rf", "T", "tR", "Rt"):
    assert_compiles(f"{prefix}'x'\n")
for prefix in ("ub", "ur", "uf", "bu", "bf", "fb", "ft", "tb", "rr", "bb"):
    assert_syntax_error(f"{prefix}'x'\n")
# shortstring cannot span lines; longstring can; escapeseq takes any code point.
assert_syntax_error("'a\nb'\n")
assert_eq(eval("'''a\nb'''"), "a\nb")
assert_eq(eval(r"'\''"), "'")
assert_eq(eval("r'\\''"), "\\'")

# integer
for text, value in (("0", 0), ("00", 0), ("0_0", 0), ("1_000", 1000), ("0b1_0", 2),
                    ("0B11", 3), ("0o1_7", 15), ("0O7", 7), ("0x_f", 15), ("0XfF", 255)):
    assert_eq(eval(text), value)
for bad in ("01", "1__0", "1_", "0b", "0b2", "0o8", "0xg", "0_1", "0x_"):
    assert_syntax_error(bad, "eval")
# floatnumber and imagnumber
for text, value in (("1.", 1.0), (".5", 0.5), ("1_0.5", 10.5), ("1e3", 1000.0), ("1.e-1", 0.1),
                    ("1_0E+1_0", 1e11), ("00.5", 0.5), ("09.5", 9.5), ("09e1", 90.0)):
    assert_eq(eval(text), value)
for text, value in (("1j", 1j), ("1.5J", 1.5j), ("01j", 1j), ("1_0j", 10j), ("1e1j", 10j)):
    assert_eq(eval(text), value)
for bad in ("1._5", "1e", "1e_1", "1_.5", "1.5_", "1_e1", "1j_"):
    assert_syntax_error(bad, "eval")
