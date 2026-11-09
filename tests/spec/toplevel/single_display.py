# spec: PLS-315 14.1, 17.6.2, B.3.4
# description: Interactive input passes the value of each expression
# statement, None too, to the display hook in order, inside its loops and
# conditionals but not in the bodies of its functions and classes; a
# Python hook runs as a call whose own expression statements display
# nothing, its exception ends the input, a native hook is called too, and
# exec and eval of the input return None.
from harness import *

shown = []

def spin():
    for _ in range(3): pass

def hook(value):
    spin()
    value
    if value == "bad": raise KeyError(value)
    shown.append(value)

def run(source, env=None, display=hook):
    saved = host.display_hook()
    host.set_display_hook(display)
    try:
        return exec(compile(source, "<input>", "single"), {"spin": spin} if env is None else env)
    finally:
        host.set_display_hook(saved)

def results():
    del shown[:]
    out = [run("1 + 1\n"), run("None\n"), run("for i in range(3): i\n"), run("if 1:\n    spin()\n    'a'\nelse:\n    'b'\n\n")]
    out.append(run("def f():\n    'not shown'\n    return 4\n\n"))
    env = {"spin": spin}
    run("class C:\n    'doc'\n    5\n    x = 6\n\n", env)
    out += [env["C"].x, run("x = 7; x; x + 1\n", env), run("for i in range(2): i * 10\n", display=shown.append)]
    try:
        run("'bad'; 'after'\n")
    except KeyError as e:
        out.append(e.args)
    saved = host.display_hook()
    host.set_display_hook(hook)
    try:
        out.append(eval(compile("8\n", "<input>", "single")))
    finally:
        host.set_display_hook(saved)
    out.append(list(shown))
    return out

expected = [None, None, None, None, None, 6, None, None, ("bad",), None, [2, None, 0, 1, 2, None, "a", 7, 8, 0, 10, 8]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
