# spec: PLS-315 24.3
# description: Programs on bytes and bytearray, each with the output CPython 3.15 gives.
from harness import *

check_program('''print('a' 'b', 'ab' * 3, 3 * 'x', 'a' + 'b', len('hé🙂'), 'hé🙂'[2])
''',
              '''ab ababab xxx ab 3 🙂
''')

check_program("print(len('a\\x00b'), 'a\\x00b'[1] == '\\x00', 'b' in 'a\\x00b')\n",
              '''3 True True
''')

check_program('''print('bc' in 'abcd', 'xy' not in 'abcd', '' in '', 'a' < 'b')
''',
              '''True True True True
''')

check_program('''d = {'a': 1, 'b': 2}; d['c'] = 3; d['a'] += 4; print(d, d['a'])
''',
              '''{'a': 5, 'b': 2, 'c': 3} 5
''')

check_program('''d = {'a': 1, 'b': 2}; print(d.get('x'), d.get('x', 8), list(d.keys()), list(d.values()), list(d.items()))
''',
              '''None 8 ['a', 'b'] [1, 2] [('a', 1), ('b', 2)]
''')

check_program('''print({'a': [1], 'b': 2} == {'b': 2, 'a': [1]}, {} == {}, {} != {'a': 1})
''',
              '''True True True
''')

check_program('''print('**{{{}: {}}}'.format(1, 2)); print('{1}:{0}:{1}'.format('a', 'b'))
''',
              '''**{1: 2}
b:a:b
''')

check_program('''print(sorted({1, *range(4)}), {**{'a': 1}, 'b': 2, **{'a': 3}})
''',
              '''[0, 1, 2, 3] {'a': 3, 'b': 2}
''')

check_program('''d = {'a': 1}
print(d.update([('b', 2)], a=3), d)
print('{!r} {name:>4}'.format('x', name='y'))
''',
              '''None {'a': 3, 'b': 2}
'x'    y
''')

check_program('''b'é'
''',
              '''SyntaxError: bytes can only contain ASCII literal characters (<program>, line 1)
''')

check_program('''b'a' 'b'
''',
              '''SyntaxError: cannot mix bytes and nonbytes literals (<program>, line 1)
''')

check_program(''''a' b'b'
''',
              '''SyntaxError: cannot mix bytes and nonbytes literals (<program>, line 1)
''')

check_program("b'\\x0'\n",
              'SyntaxError: (value error) invalid \\x escape at position 0 (<program>, line 1)\n')

check_program('''bytes([-1])
''',
              '''ValueError: bytes must be in range(0, 256)
''')

check_program('''bytes([256])
''',
              '''ValueError: bytes must be in range(0, 256)
''')

check_program('''bytes([2**100])
''',
              '''ValueError: bytes must be in range(0, 256)
''')

check_program('''bytes([1.0])
''',
              '''TypeError: 'float' object cannot be interpreted as an integer
''')

check_program('''bytes(-1)
''',
              '''ValueError: negative count
''')

check_program('''bytes('abc')
''',
              '''TypeError: string argument without an encoding
''')

check_program('''b'a' + 'b'
''',
              '''TypeError: can't concat str to bytes
''')
