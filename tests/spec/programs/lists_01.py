# spec: PLS-315 25.1
# description: Programs on lists, each with the output CPython 3.15 gives.
from harness import *

check_program('''print(None, True, False, bool([]), bool([0]))
''',
              '''None True False False True
''')

check_program('''print(0 and missing, 4 or missing, not 1 == 2, not [] and True)
''',
              '''0 4 True True
''')

check_program('''print([1, 2] + [3], [1] * 3, (1, 2) + (3,), (1,) * 2)
''',
              '''[1, 2, 3] [1, 1, 1] (1, 2, 3) (1, 1)
''')

check_program('''print([1, 2] == [1, 2], [1] != [2], (1,) != [1], [] == [])
''',
              '''True True True True
''')

check_program('''a = [1, 2, 3]; a[-1] = 7; a.append(9); print(a, a.pop(), a.pop(0), a)
''',
              '''[2, 7] 9 1 [2, 7]
''')

check_program('''a = []; a.append(a); print(a)
''',
              '''[[...]]
''')

check_program('''a = []; b = a; a += [1, 2]; print(a, b, a is b)
''',
              '''[1, 2] [1, 2] True
''')

check_program('''a = [1, 2]; a += a; print(a)
''',
              '''[1, 2, 1, 2]
''')

check_program('''a = [1, 2]; b = a; a *= 3; print(a, a is b)
a += iter((7, 8)); print(a)
a *= 0; print(a, b, a is b)
a.append(a); a *= 2; print(a)
''',
              '''[1, 2, 1, 2, 1, 2] True
[1, 2, 1, 2, 1, 2, 7, 8]
[] [] True
[[...], [...]]
''')

check_program('''d = {}; d['self'] = d; print(d)
''',
              '''{'self': {...}}
''')

check_program('''print(all([]), any([]), all([1, 2]), any([0, 3]), all([0, 1]))
''',
              '''True False True True False
''')

check_program('''print(type(True), type(1), type([]), type(type), isinstance(True, int), issubclass(bool, int))
''',
              '''<class 'bool'> <class 'int'> <class 'list'> <class 'type'> True True
''')

check_program('''print(type(None), type((i for i in []))); a = None; b = None; print(id(a) == id(b), id(True) == id(True))
''',
              '''<class 'NoneType'> <class 'generator'>
True True
''')

check_program('''a = b = []; a.append(1); print(a is b, b); a, b = b, a; print(a is b)
''',
              '''True [1]
True
''')

check_program('''i = 0; a = [0, 0]; i, a[i] = 1, 5; print(i, a)
''',
              '''1 [0, 5]
''')

check_program('''it = iter([1]); print(next(it), next(it, 42), next(it, 43)); print(iter(it) is it)
''',
              '''1 42 43
True
''')

check_program('''print(list(reversed([1, 2, 3])), list(reversed('hé🙂')), sorted([(2, 0), (1, 2), (1, 1)]))
''',
              '''[3, 2, 1] ['🙂', 'é', 'h'] [(1, 1), (1, 2), (2, 0)]
''')

check_program('''aiter([])
''',
              '''TypeError: 'list' object is not an async iterable
''')

check_program('''anext(iter([]))
''',
              '''TypeError: 'list_iterator' object is not an async iterator
''')

check_program('''async for x in []:
    pass
''',
              '''SyntaxError: 'async for' outside async function (<program>, line 1)
''')
