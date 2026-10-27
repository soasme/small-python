# spec: PLS-315 23.1, 24.2
# description: Programs on strings, each with the output CPython 3.15 gives.
from harness import *

check_program('''print(str(ValueError('message')), repr(ValueError('message')), str(KeyError('key')))
''',
              '''message ValueError('message') 'key'
''')

check_program('''','.join(['a', 1])
''',
              '''TypeError: sequence item 1: expected str instance, int found
''')

check_program('''
class Index:
    def __init__(self, array, replacement, value):
        self.array, self.replacement, self.value = array, replacement, value
    def __index__(self):
        self.array.clear()
        self.array.extend(self.replacement)
        return self.value
for initial in [b'', b'abc', b'abcdef']:
    for replacement in [b'', b'X', b'XYZW']:
        for operation in range(8):
            a = bytearray(initial)
            index = Index(a, replacement, 0)
            value = Index(a, replacement, 88)
            try:
                if operation == 0: a[0] = value
                elif operation == 1: a[index] = 89
                elif operation == 2: a.append(value)
                elif operation == 3: print('pop', a.pop(index))
                elif operation == 4: a.insert(index, value)
                elif operation == 5: a.remove(value)
                elif operation == 6: del a[index]
                else: a.extend([value])
            except Exception as error: print(type(error).__name__)
            print(a)
for step in [1, 2, -1, -2]:
    for replacement in [b'', b'X', b'XYZW']:
        a = bytearray(b'abc')
        start = Index(a, replacement, 0)
        try: del a[start::step]
        except Exception as error: print(type(error).__name__)
        print(a)
        a = bytearray(b'abc')
        start = Index(a, replacement, 0)
        try: a[start::step] = b'XY'
        except Exception as error: print(type(error).__name__)
        print(a)
a = bytearray(b'abc')
a[:] = a
print(a)
del a[::2]
print(a)
for obj in ['', b'', bytearray()]:
    for method in ['center', 'join', 'partition', 'removeprefix', 'translate']:
        try: getattr(obj, method)()
        except TypeError: print('missing argument')
        try: getattr(obj, method)(unexpected=1)
        except TypeError: print('unexpected keyword')
for method in ['append', 'extend', 'insert', 'remove']:
    try: getattr(bytearray(), method)()
    except TypeError: print('missing bytearray argument')
    try: getattr(bytearray(), method)(unexpected=1)
    except TypeError: print('unexpected bytearray keyword')
''',
              '''IndexError
bytearray(b'')
IndexError
bytearray(b'')
bytearray(b'X')
IndexError
bytearray(b'')
bytearray(b'X')
ValueError
bytearray(b'')
IndexError
bytearray(b'')
bytearray(b'X')
bytearray(b'X')
bytearray(b'Y')
bytearray(b'XX')
pop 88
bytearray(b'')
bytearray(b'XX')
bytearray(b'')
bytearray(b'')
bytearray(b'XX')
bytearray(b'XYZW')
bytearray(b'YYZW')
bytearray(b'XYZWX')
pop 88
bytearray(b'YZW')
bytearray(b'XXYZW')
bytearray(b'YZW')
bytearray(b'YZW')
bytearray(b'XYZWX')
IndexError
bytearray(b'')
IndexError
bytearray(b'')
bytearray(b'X')
IndexError
bytearray(b'')
bytearray(b'X')
ValueError
bytearray(b'')
IndexError
bytearray(b'')
bytearray(b'X')
bytearray(b'X')
bytearray(b'Y')
bytearray(b'XX')
pop 88
bytearray(b'')
bytearray(b'XX')
bytearray(b'')
bytearray(b'')
bytearray(b'XX')
bytearray(b'XYZW')
bytearray(b'YYZW')
bytearray(b'XYZWX')
pop 88
bytearray(b'YZW')
bytearray(b'XXYZW')
bytearray(b'YZW')
bytearray(b'YZW')
bytearray(b'XYZWX')
IndexError
bytearray(b'')
IndexError
bytearray(b'')
bytearray(b'X')
IndexError
bytearray(b'')
bytearray(b'X')
ValueError
bytearray(b'')
IndexError
bytearray(b'')
bytearray(b'X')
bytearray(b'X')
bytearray(b'Y')
bytearray(b'XX')
pop 88
bytearray(b'')
bytearray(b'XX')
bytearray(b'')
bytearray(b'')
bytearray(b'XX')
bytearray(b'XYZW')
bytearray(b'YYZW')
bytearray(b'XYZWX')
pop 88
bytearray(b'YZW')
bytearray(b'XXYZW')
bytearray(b'YZW')
bytearray(b'YZW')
bytearray(b'XYZWX')
bytearray(b'')
bytearray(b'XY')
bytearray(b'')
bytearray(b'XY')
bytearray(b'')
bytearray(b'XY')
bytearray(b'')
ValueError
bytearray(b'')
bytearray(b'')
ValueError
bytearray(b'X')
bytearray(b'YW')
bytearray(b'XYYW')
bytearray(b'')
ValueError
bytearray(b'')
bytearray(b'')
ValueError
bytearray(b'X')
bytearray(b'YZW')
ValueError
bytearray(b'XYZW')
bytearray(b'')
ValueError
bytearray(b'')
bytearray(b'')
ValueError
bytearray(b'X')
bytearray(b'YZW')
ValueError
bytearray(b'XYZW')
bytearray(b'abc')
bytearray(b'b')
missing argument
unexpected keyword
missing argument
unexpected keyword
missing argument
unexpected keyword
missing argument
unexpected keyword
missing argument
unexpected keyword
missing argument
unexpected keyword
missing argument
unexpected keyword
missing argument
unexpected keyword
missing argument
unexpected keyword
missing argument
unexpected keyword
missing argument
unexpected keyword
missing argument
unexpected keyword
missing argument
unexpected keyword
missing argument
unexpected keyword
missing argument
unexpected keyword
missing bytearray argument
unexpected bytearray keyword
missing bytearray argument
unexpected bytearray keyword
missing bytearray argument
unexpected bytearray keyword
missing bytearray argument
unexpected bytearray keyword
''')

check_program('''
def take(target, replacement, n):
    class Evil:
        def __index__(self):
            target.clear()
            target.extend(replacement)
            return n
    return target.take_bytes(Evil())
for initial in [b'', b'a', b'abcdefgh']:
    for replacement in [b'', b'xy', b'abcdefghij']:
        for n in [-12, -3, -1, 0, 1, 3, 8, 11]:
            a = bytearray(initial)
            try: print(take(a, replacement, n))
            except Exception as error: print(type(error).__name__)
            print(a)
for n in [None, 0, 1, -1, 10**100, -10**100, 3.14, 'x']:
    a = bytearray(b'abc')
    try: print(a.take_bytes(n))
    except Exception as error: print(type(error).__name__)
    print(a)
class Array(bytearray): pass
for cls in [bytearray, Array]:
    a = cls(b'abcdef')
    print(a.take_bytes(2), a.take_bytes(-1), a.take_bytes(), bytes(a))
    for n in [10, 3, 0, 7, -1, 3.5]:
        try: print(a.resize(n))
        except Exception as error: print(type(error).__name__)
        print(bytes(a))
for step in [-3, -1, 1, 2, 3]:
    a = bytearray(b'abcdefgh')
    a[::step] = b''
    print(a)
''',
              "IndexError\nbytearray(b'')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'')\nb''\nbytearray(b'')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'xy')\nIndexError\nbytearray(b'xy')\nb'x'\nbytearray(b'y')\nb''\nbytearray(b'xy')\nb'x'\nbytearray(b'y')\nIndexError\nbytearray(b'xy')\nIndexError\nbytearray(b'xy')\nIndexError\nbytearray(b'xy')\nIndexError\nbytearray(b'abcdefghij')\nb'abcdefg'\nbytearray(b'hij')\nb'abcdefghi'\nbytearray(b'j')\nb''\nbytearray(b'abcdefghij')\nb'a'\nbytearray(b'bcdefghij')\nb'abc'\nbytearray(b'defghij')\nb'abcdefgh'\nbytearray(b'ij')\nIndexError\nbytearray(b'abcdefghij')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'')\nb''\nbytearray(b'')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'xy')\nIndexError\nbytearray(b'xy')\nb'x'\nbytearray(b'y')\nb''\nbytearray(b'xy')\nb'x'\nbytearray(b'y')\nIndexError\nbytearray(b'xy')\nIndexError\nbytearray(b'xy')\nIndexError\nbytearray(b'xy')\nIndexError\nbytearray(b'abcdefghij')\nb'abcdefg'\nbytearray(b'hij')\nb'abcdefghi'\nbytearray(b'j')\nb''\nbytearray(b'abcdefghij')\nb'a'\nbytearray(b'bcdefghij')\nb'abc'\nbytearray(b'defghij')\nb'abcdefgh'\nbytearray(b'ij')\nIndexError\nbytearray(b'abcdefghij')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'')\nb''\nbytearray(b'')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'')\nIndexError\nbytearray(b'xy')\nIndexError\nbytearray(b'xy')\nb'x'\nbytearray(b'y')\nb''\nbytearray(b'xy')\nb'x'\nbytearray(b'y')\nIndexError\nbytearray(b'xy')\nIndexError\nbytearray(b'xy')\nIndexError\nbytearray(b'xy')\nIndexError\nbytearray(b'abcdefghij')\nb'abcdefg'\nbytearray(b'hij')\nb'abcdefghi'\nbytearray(b'j')\nb''\nbytearray(b'abcdefghij')\nb'a'\nbytearray(b'bcdefghij')\nb'abc'\nbytearray(b'defghij')\nb'abcdefgh'\nbytearray(b'ij')\nIndexError\nbytearray(b'abcdefghij')\nb'abc'\nbytearray(b'')\nb''\nbytearray(b'abc')\nb'a'\nbytearray(b'bc')\nb'ab'\nbytearray(b'c')\nIndexError\nbytearray(b'abc')\nIndexError\nbytearray(b'abc')\nTypeError\nbytearray(b'abc')\nTypeError\nbytearray(b'abc')\nb'ab' b'cde' b'f' b''\nNone\nb'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\nNone\nb'\\x00\\x00\\x00'\nNone\nb''\nNone\nb'\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\nValueError\nb'\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\nTypeError\nb'\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\nb'ab' b'cde' b'f' b''\nNone\nb'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\nNone\nb'\\x00\\x00\\x00'\nNone\nb''\nNone\nb'\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\nValueError\nb'\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\nTypeError\nb'\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\nbytearray(b'acdfg')\nbytearray(b'')\nbytearray(b'')\nbytearray(b'bdfh')\nbytearray(b'bcefh')\n")

check_program("def show(thunk):\n    try:\n        print(repr(thunk()))\n    except Exception as error:\n        print(type(error).__name__)\nshow(lambda: ('.σAéé1İ,ǆba'.upper()))\nshow(lambda: ('. _a--\\t1'.rsplit('b,', maxsplit=-1)))\nshow(lambda: ('İé .Aǆ1aA,'.partition(','), 'İé .Aǆ1aA,'.rpartition(',')))\nshow(lambda: ('ǆǆ 1\\tA.Σ.'.center(13, '*'), 'ǆǆ 1\\tA.Σ.'.ljust(13), 'ǆǆ 1\\tA.Σ.'.rjust(13, '-')))\nshow(lambda: (' ǆé, σ_ǆ'.split('', -1)))\nshow(lambda: ('1éé'.replace('  ', 'XY', -1)))\nshow(lambda: (''.strip(','), ''.removeprefix(','), ''.removesuffix(',')))\nshow(lambda: ('A'.expandtabs(3)))\nshow(lambda: ('\\nσB.Σ'.rsplit('', maxsplit=-1)))\nshow(lambda: (',--İσ\\tΣ-Σ_ß'.partition('b'), ',--İσ\\tΣ-Σ_ß'.rpartition('b')))\nshow(lambda: ('\\t-ǆ,1...\\t'.center(19, '*'), '\\t-ǆ,1...\\t'.ljust(19), '\\t-ǆ,1...\\t'.rjust(19, '-')))\nshow(lambda: (''.split('', 1)))\nshow(lambda: ('Bİbσ,Aßßσ'.replace('', 'XY', 0)))\nshow(lambda: ('1ΣΣ'.strip(''), '1ΣΣ'.removeprefix(''), '1ΣΣ'.removesuffix('')))\nshow(lambda: ('1_'.encode('ascii', 'backslashreplace')))\nshow(lambda: ('1\\n_σ--ΣAǆaa'.rsplit('b,', maxsplit=-1)))\nshow(lambda: ('\\tBé'.partition(''), '\\tBé'.rpartition('')))\nshow(lambda: ('.\\nǆ Σ1Σ\\t1σ\\t'.center(3, '*'), '.\\nǆ Σ1Σ\\t1σ\\t'.ljust(3), '.\\nǆ Σ1Σ\\t1σ\\t'.rjust(3, '-')))\nshow(lambda: ('BB \\n1Σ'.split('a', -1)))\nshow(lambda: ('b\\t 1ßΣ'.replace('a', 'XY', 2)))\nshow(lambda: ('B1σ'.strip('ba'), 'B1σ'.removeprefix('ba'), 'B1σ'.removesuffix('ba')))\nshow(lambda: ('Aé\\t\\tİ\\n1ǆ-'.isascii()))\nshow(lambda: (''.rsplit('', maxsplit=-1)))\nshow(lambda: ('ß\\n.1,'.partition('a '), 'ß\\n.1,'.rpartition('a ')))\nshow(lambda: ('\\t'.center(2, '*'), '\\t'.ljust(2), '\\t'.rjust(2, '-')))\nshow(lambda: (b'\\tb '.split(b' ,'), b'\\tb '.replace(b' ,', b'-'), b'\\tb '.partition(b' ,')))\nshow(lambda: (b'b'.split(b''), b'b'.replace(b'', b'-'), b'b'.partition(b'')))\nshow(lambda: (b'a'.split(b'a'), b'a'.replace(b'a', b'-'), b'a'.partition(b'a')))\nshow(lambda: (b'bA\\n.'.split(b' a'), b'bA\\n.'.replace(b' a', b'-'), b'bA\\n.'.partition(b' a')))\nshow(lambda: (b'aA..b'.split(b' a'), b'aA..b'.replace(b' a', b'-'), b'aA..b'.partition(b' a')))\nshow(lambda: (sorted(set([4, 7]) | set([3, 4, 7])), sorted(set([4, 7]) & set([3, 4, 7]))))\nshow(lambda: (set([4]) <= set([0, 5, 7]), set([4]) < set([0, 5, 7]), set([4]).isdisjoint([0, 5, 7]), frozenset([4]) == set([4])))\nshow(lambda: (sorted(set([2, 6]) | set([0, 7])), sorted(set([2, 6]) & set([0, 7]))))\nshow(lambda: (set([]) <= set([0, 1, 2]), set([]) < set([0, 1, 2]), set([]).isdisjoint([0, 1, 2]), frozenset([]) == set([])))\nshow(lambda: (sorted(set([0, 2, 4, 6]) | set([3])), sorted(set([0, 2, 4, 6]) & set([3]))))\nshow(lambda: (set([3, 5, 7]) <= set([1]), set([3, 5, 7]) < set([1]), set([3, 5, 7]).isdisjoint([1]), frozenset([3, 5, 7]) == set([3, 5, 7])))\nshow(lambda: (sorted(set([1, 2, 4]) | set([])), sorted(set([1, 2, 4]) & set([]))))\nshow(lambda: ((-496027029612).to_bytes(6, 'big', signed=True)))\nshow(lambda: ((-880168777).to_bytes(10, 'little', signed=True)))\nshow(lambda: ((1746080865).to_bytes(9, 'big', signed=True)))\nshow(lambda: ((7075010).to_bytes(6, 'little', signed=True)))\nshow(lambda: ((51874194445806010271610).to_bytes(4, 'big', signed=True)))\nshow(lambda: ((-22856941512503011419599).to_bytes(8, 'big', signed=True)))\nshow(lambda: (b'\\xff'.decode()))\n",
              "'.ΣAÉÉ1İ,ǄBA'\n['. _a--\\t1']\n(('İé .Aǆ1aA', ',', ''), ('İé .Aǆ1aA', ',', ''))\n('**ǆǆ 1\\tA.Σ.**', 'ǆǆ 1\\tA.Σ.    ', '----ǆǆ 1\\tA.Σ.')\nValueError\n'1éé'\n('', '', '')\n'A'\nValueError\n((',--İσ\\tΣ-Σ_ß', '', ''), ('', '', ',--İσ\\tΣ-Σ_ß'))\n('*****\\t-ǆ,1...\\t*****', '\\t-ǆ,1...\\t          ', '----------\\t-ǆ,1...\\t')\nValueError\n'Bİbσ,Aßßσ'\n('1ΣΣ', '1ΣΣ', '1ΣΣ')\nb'1_'\n['1\\n_σ--ΣAǆaa']\nValueError\n('.\\nǆ Σ1Σ\\t1σ\\t', '.\\nǆ Σ1Σ\\t1σ\\t', '.\\nǆ Σ1Σ\\t1σ\\t')\n['BB \\n1Σ']\n'b\\t 1ßΣ'\n('B1σ', 'B1σ', 'B1σ')\nFalse\nValueError\n(('ß\\n.1,', '', ''), ('', '', 'ß\\n.1,'))\n('\\t*', '\\t ', '-\\t')\n([b'\\tb '], b'\\tb ', (b'\\tb ', b'', b''))\nValueError\n([b'', b''], b'-', (b'', b'a', b''))\n([b'bA\\n.'], b'bA\\n.', (b'bA\\n.', b'', b''))\n([b'aA..b'], b'aA..b', (b'aA..b', b'', b''))\n([3, 4, 7], [4, 7])\n(False, False, True, True)\n([0, 2, 6, 7], [])\n(True, True, True, True)\n([0, 2, 3, 4, 6], [])\n(False, False, True, True)\n([1, 2, 4], [])\nb'\\xff\\x8c\\x82|/\\x94'\nb'\\xb7\\xb0\\x89\\xcb\\xff\\xff\\xff\\xff\\xff\\xff'\nb'\\x00\\x00\\x00\\x00\\x00h\\x13\\x14a'\nb'\\xc2\\xf4k\\x00\\x00\\x00'\nOverflowError\nOverflowError\nUnicodeDecodeError\n")
