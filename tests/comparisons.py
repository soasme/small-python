"""Rich-comparison dispatch matrix, supplementing CPython test_compare.py."""

from pathlib import Path
import itertools
import subprocess
import sys


METHODS = ['__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__']
OPERATORS = ['<', '<=', '==', '!=', '>', '>=']
GROUPS = [(), ('__eq__',), ('__ne__',), ('__eq__', '__ne__'),
          ('__lt__',), ('__gt__',), ('__le__', '__ge__'), tuple(METHODS)]


def definition(name, base, methods, result):
    lines = [f'class {name}({base}):']
    for method in methods:
        lines.extend([f'    def {method}(self, other):',
                      f'        calls.append({(name + method)!r})',
                      f'        return {result}'])
    return '\n'.join(lines if methods else lines + ['    pass']) + '\n'


def main():
    engine = str(Path(sys.argv[1]).resolve())
    count = 0
    for left, right, derived, answer in itertools.product(GROUPS, GROUPS, [False, True], ['NotImplemented', "['value']"]):
        source = 'calls = []\n' + definition('Left', 'object', left, 'NotImplemented')
        source += definition('Right', 'Left' if derived else 'object', right, answer)
        source += 'a = Left(); b = Right()\n'
        for operator in OPERATORS:
            source += f"calls = []\ntry: print(a {operator} b)\nexcept TypeError: print('TypeError')\nprint(calls)\n"
        expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True, text=True, timeout=10)
        actual = subprocess.run([engine, '-c', source], capture_output=True, text=True, timeout=10)
        if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
            raise AssertionError(f'{source}\nCPython:\n{expected.stdout}{expected.stderr}\nspy:\n{actual.stdout}{actual.stderr}')
        count += len(OPERATORS)
    source = '''
nan = float('nan')
values = [slice(1), slice(1, 2), slice(1, 2, 3), slice(1, 2, 4), slice(None),
          slice(nan), slice(nan), slice(float('nan')), slice([], []), slice([1], [2])]
for a in values:
    for b in values:
'''
    for operator in OPERATORS:
        source += f"        try: print(a {operator} b)\n        except TypeError: print('TypeError')\n"
    expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True, text=True, timeout=10)
    actual = subprocess.run([engine, '-c', source], capture_output=True, text=True, timeout=10)
    if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
        raise AssertionError(f'Slice comparisons\nCPython:\n{expected.stdout}{expected.stderr}\nspy:\n{actual.stdout}{actual.stderr}')
    print(f'Comparisons: {count} method-dispatch and 600 slice checks passed')


if __name__ == '__main__':
    main()
