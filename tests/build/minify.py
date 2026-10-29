# build: --minify
# bundles: minify.py shapes.py
# description: --minify removes comments and spaces but keeps strings, tokens, and every line number.
import shapes   # bundled and minified too


def area(w, h):
    # a comment
    return w * h


text = """keep   this
    # not a comment
  indentation"""
assert text == "keep   this\n    # not a comment\n  indentation"
assert f"{1 + 1:>4}" == "   2" and f"{'#'}" == "#"
total = (1 +
         2)
value = 1 \
    + 2
assert total == value == 3
assert 1 .real == 1 and [i for i in range(3) if i] == [1, 2]
x = 1 if area(2, 3) == 6 else 2
assert x == 1


def fail():
    raise ValueError("line")


try:
    fail()
except ValueError as error:
    assert error.__traceback__.tb_next.tb_lineno == 28
try:
    shapes.square(None)
except TypeError as error:
    assert error.__traceback__.tb_next.tb_lineno == 3
assert shapes.square(3) == 9
