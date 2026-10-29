# build: -O
# bundles: optimize.py checks.py
# description: -O removes assert statements and makes __debug__ false, as python -O does, and keeps every line number.
import checks
assert False, "removed"
if __debug__:
    raise SystemExit("__debug__ is true")
if (lambda: __debug__)():
    raise SystemExit("__debug__ is true in a lambda")
if f"{__debug__}" != "False":
    raise SystemExit("__debug__ is true in an f-string")
if True: assert False
assert False; reached = True


def boom():
    raise ValueError


try:
    boom()
except ValueError as error:
    if error.__traceback__.tb_next.tb_lineno != 17:
        raise SystemExit("line numbers moved")
if not reached or checks.run() != "ran":
    raise SystemExit("an assert took more than itself")
