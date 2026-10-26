"""Async protocol differential checks; these are not upstream test ports.

The state transitions are informed by the pinned CPython test_asyncgen.py
tests for concurrent asend/athrow, operation reuse, and aclose after exhaustion.
Run with the pinned 3.15 interpreter to check this version's close semantics.
"""

from pathlib import Path
import itertools
import subprocess
import sys


ENGINE = str(Path(sys.argv[1]).resolve())
PRELUDE = """
class Pause:
    def __await__(self):
        try:
            yield 'waiting'
        except ValueError:
            return 'caught await'
        return 'resumed'
async def values():
    try:
        try:
            sent = yield 'first'
            print('sent', sent)
            yield await Pause()
        except ValueError:
            yield 'caught generator'
    finally:
        await Pause()
        print('cleanup')
def drive(operation, action):
    try:
        if action == 'next': result = next(operation)
        elif action == 'send': result = operation.send(42)
        elif action == 'throw': result = operation.throw(ValueError('injected'))
        elif action == 'exit': result = operation.throw(GeneratorExit)
        else: result = operation.close()
        print('result', result)
    except BaseException as error:
        print('error', type(error).__name__, error.args)
g = values()
"""

STATES = {
    'created': '',
    'yielded': "drive(g.__anext__(), 'next')\n",
    'awaiting': "drive(g.__anext__(), 'next')\nowner = g.asend(None)\ndrive(owner, 'next')\n",
    'exhausted': "owner = g.__anext__()\ndrive(owner, 'next')\nowner = g.aclose()\ndrive(owner, 'next')\ndrive(owner, 'next')\n",
}
OPERATIONS = ['g.__anext__()', 'g.asend(None)', 'g.asend(7)',
              'g.athrow(ValueError)', 'g.athrow(GeneratorExit)', 'g.aclose()']
ACTIONS = ['next', 'send', 'throw', 'exit', 'close']


def run(command, source):
    return subprocess.run([*command, '-c', source], capture_output=True,
                          text=True, timeout=10)


def main():
    if sys.version_info[:2] != (3, 15):
        raise SystemExit('Use the pinned Python 3.15 development oracle')
    count = 0
    for (state, setup), operation, action in itertools.product(STATES.items(), OPERATIONS, ACTIONS):
        source = PRELUDE + setup + f"op = {operation}\ndrive(op, {action!r})\ndrive(op, 'next')\nprint('running', g.ag_running)\n"
        expected = run([sys.executable, '-I'], source)
        actual = run([ENGINE], source)
        if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
            raise AssertionError(
                f'{state}, {operation}, {action}\n{source}\n'
                f'CPython ({expected.returncode}):\n{expected.stdout}{expected.stderr}\n'
                f'spy ({actual.returncode}):\n{actual.stdout}{actual.stderr}')
        count += 1
    print(f'Async: {count} operation/state combinations passed')


if __name__ == '__main__':
    main()
