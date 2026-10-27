# spec: PLS-315 16.4
# description: Programs on class definitions, each with the output CPython 3.15 gives.
from harness import *

check_program('''big = 10**100
for r in [range(5), range(2, 8, 2), range(big, big + 10, 3), range(-big, -big - 10, -3), range(5, 5, -1)]:
    print(r, r.start, r.stop, r.step, len(r), bool(r))
    print(list(r), list(reversed(r)), list(r[::-1]), r[1:-1], r[::-2])
    if r:
        print(r[0], r[-1], r[0] in r, r.stop in r, r.count(r[0]), r.index(r[-1]))
r = range(-big, big, 3)
print(r[big // 3], r[-1], next(reversed(r)), r[:5], r[-5:], r[::big])
print(r.count(-big), r.index(-big + 3 * 10**90), r.count(big))
print(range(0) == range(2, 2, -3), range(0, 3, 2) == range(0, 4, 2), range(1) == range(0, 1, 9))
print(range(5).count(2.0), range(5).index(2.0), range(5).count('2'))
print(slice(None, None, -1).indices(big), slice(-big * 2, big * 2, big).indices(big))
print(slice(-big * 2, big * 2, -big).indices(big), slice(None, None, big).indices(5))
class Index:
    def __index__(self): return big
print(range(Index(), big + 2), list(range(Index(), big + 2)))
''',
              '''range(0, 5) 0 5 1 5 True
[0, 1, 2, 3, 4] [4, 3, 2, 1, 0] [4, 3, 2, 1, 0] range(1, 4) range(4, -1, -2)
0 4 True False 1 4
range(2, 8, 2) 2 8 2 3 True
[2, 4, 6] [6, 4, 2] [6, 4, 2] range(4, 6, 2) range(6, 0, -4)
2 6 True False 1 2
range(10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010, 3) 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010 3 4 True
[10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009] [10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000] [10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000] range(10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009, 3) range(10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009, 9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999997, -6)
10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009 True False 1 3
range(-10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000, -10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010, -3) -10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 -10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010 -3 4 True
[-10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000, -10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003, -10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006, -10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009] [-10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009, -10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006, -10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003, -10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000] [-10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009, -10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006, -10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003, -10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000] range(-10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003, -10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009, -3) range(-10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009, -9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999997, 6)
-10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 -10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009 True False 1 3
range(5, 5, -1) 5 5 -1 0 False
[] [] [] range(5, 5, -1) range(6, 6, 2)
-1 9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999998 9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999998 range(-10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000, -9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999985, 3) range(9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999986, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001, 3) range(-10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001, 30000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000)
1 1000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 0
True True True
1 2 0
(9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999, -1, -1) (0, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000)
(-1, 9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999, -10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000) (0, 5, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000)
range(10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002) [10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000, 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001]
''')

check_program('a = b\'\\x00\\x7f\\x80\\xff\\n\\t\\r\\\'"\'\nprint(a, str(a), repr(a), len(a), list(a), tuple(reversed(a)))\nprint(a[0], a[-1], a[1:-1], a[::-2], a[:0])\nprint(a + b\'z\', b\'ab\' * 3, 2 * b\'x\', b\'x\' * 0, bool(b\'\'), bool(a))\nprint(b\'a\' < b\'b\', b\'a\' == \'a\', b\'a\' != \'a\', b\'\\xff\' > b\'z\')\nprint(0 in a, 255 in a, b\'\\x7f\\x80\' in a, b\'\' in a, b\'zz\' not in a)\nprint(B\'ab\' b\'cd\', br\'\\xff\', RB\'\\n\', b\'\\101\\377\', ord(b\'\\xff\'))\nprint(bytes(), bytes(3), bytes([0, 127, 128, 255]), bytes(range(3)), bytes(a) is a)\nprint(int(b\'123456789012345678901234567890\'), int(b\'ff\', 16), float(b\'2.5\'))\nprint({b\'x\': 1, b\'y\': 2}[b\'x\'], b\'x\' in {b\'x\': 1})\nclass Byte:\n    def __index__(self): return 65\nclass ByteSource:\n    def __bytes__(self): return b\'converted\'\nprint(bytes([Byte()]), bytes(ByteSource()))\n',
              'b\'\\x00\\x7f\\x80\\xff\\n\\t\\r\\\'"\' b\'\\x00\\x7f\\x80\\xff\\n\\t\\r\\\'"\' b\'\\x00\\x7f\\x80\\xff\\n\\t\\r\\\'"\' 9 [0, 127, 128, 255, 10, 9, 13, 39, 34] (34, 39, 13, 9, 10, 255, 128, 127, 0)\n0 34 b"\\x7f\\x80\\xff\\n\\t\\r\'" b\'"\\r\\n\\x80\\x00\' b\'\'\nb\'\\x00\\x7f\\x80\\xff\\n\\t\\r\\\'"z\' b\'ababab\' b\'xx\' b\'\' False True\nTrue False True True\nTrue True True True True\nb\'abcd\' b\'\\\\xff\' b\'\\\\n\' b\'A\\xff\' 255\nb\'\' b\'\\x00\\x00\\x00\' b\'\\x00\\x7f\\x80\\xff\' b\'\\x00\\x01\\x02\' True\n123456789012345678901234567890 255 2.5\n1 True\nb\'A\' b\'converted\'\n')

check_program('''class Count:
    def __index__(self): return 2
a = [4]; b = a; a *= Count(); print(a, a is b)
class Base:
    def __add__(self, other): print('add'); return NotImplemented
    def __radd__(self, other): print('radd'); return 12
    def __iadd__(self, other): print('iadd'); return NotImplemented
class Sub(Base):
    def __radd__(self, other): print('sub radd'); return 14
print(Base() + Sub())
a = Base(); a += Sub(); print(a)
print(1 + Base())
class Format:
    def __rmod__(self, other): return 'wrong'
    def __str__(self): return 'formatted'
print('%s' % Format())
''',
              '''[4, 4] True
sub radd
14
iadd
sub radd
14
radd
12
formatted
''')

check_program('''class A: pass
print(list(A.__dict__))
A.__name__="B"; print(A.__name__, A.__qualname__, "__name__" in A.__dict__)
print(type("X",(),{"__qualname__":"Q.X"}).__qualname__, "__qualname__" in type("X",(),{"__qualname__":"Q"}).__dict__)
''',
              '''['__module__', '__firstlineno__', '__static_attributes__', '__dict__', '__weakref__', '__doc__']
B A False
Q.X False
''')

check_program('from __future__ import annotations\nclass A:\n    __p: Undefined[1]\n    if False:\n        q: int\n    r: str = "x"\nclass B(A): pass\nprint(A.__annotations__, B.__annotations__, A.r)\ndef g():\n    x: Nope = 1\n    return x\nprint(g(), g.__annotations__)\nns = {}\nexec("y: int = 2\\nclass C:\\n    z: \'q\'\\n", ns)\nprint(ns.get("__annotations__"), ns["C"].__annotate__)\nns = {}\nexec(compile("y: a.b\\nclass C:\\n    z: list[int]\\n", "<s>", "exec", 0x1000000), ns)\nprint(ns["__annotations__"], ns["C"].__annotations__, ns["C"].__annotate__)\ndef h(a: x.y, *, b: int = 3) -> None: pass\nimport_ok = h.__annotate__(1)\nprint(import_ok)\n',
              '''{'_A__p': 'Undefined[1]', 'r': 'str'} {} x
1 {}
{'y': 'int'} None
{'y': 'a.b'} {'z': 'list[int]'} None
{'a': 'x.y', 'b': 'int', 'return': 'None'}
''')

check_program('''class C:
    def __bool__(self): return False
    def __str__(self): return 'text'
    def __repr__(self): return 'C()'
c = C()
print(bool(c), str(c), repr(c), [c], isinstance(c, C), isinstance(c, object))
setattr(c, 'x', 3)
print(getattr(c, 'x'), getattr(c, 'missing', 4), hasattr(c, 'x'), hasattr(c, 'missing'))
del c.x
print(hasattr(c, 'x'))
''',
              '''False text C() [C()] True True
3 4 True False
False
''')

check_program('''class Base:
    value = 4
    def f(self, n=1):
        return self.value + n
class Child(Base):
    def __init__(self, value):
        self.value = value
    def __call__(self, x):
        return self.f(x)
a = Child(value=10)
method = a.f
a.value += 2
print(method(), a(3), Base.value)
''',
              '''13 15 4
''')

check_program('''x = 3
class C:
    x = 4
    def f(self):
        return x
print(C.x, C().f())
''',
              '''4 3
''')

check_program('''class Counter:
    def __init__(self, n):
        self.n = n
    def __iter__(self):
        return self
    def __next__(self):
        if not self.n:
            raise StopIteration
        self.n -= 1
        return self.n
it = Counter(4)
print(iter(it) is it, next(it), list(it), next(it, 42))
print(sum(Counter(5)), any(Counter(1)), all(Counter(2)))
''',
              '''True 3 [2, 1, 0] 42
10 False False
''')

check_program('''class Index:
    def __init__(self, n): self.n = n
    def __index__(self): print('index', self.n); return self.n
a = [0,1,2,3,4]
print(a[Index(-1)], a[Index(1):Index(4):Index(2)])
a[Index(1):Index(4):Index(2)] = [10, 30]
print(a)
class Keys:
    def __getitem__(self, key): return key
print(Keys()[1:5:2, 3], slice(2), slice(1,2,3).start, slice(1,2,3).stop, slice(1,2,3).step)
print(slice(1,2,3) == slice(1,2,3), {slice(1): 42}[slice(1)])
''',
              '''index -1
index 2
index 1
index 4
4 [1, 3]
index 2
index 1
index 4
[0, 10, 2, 30, 4]
(slice(1, 5, 2), 3) slice(None, 2, None) 1 2 3
True 42
''')

check_program('''class C:
    z = 1
    def __dir__(self):
        return ('z', 'a', 'q')
print(dir(C()))
''',
              '''['a', 'q', 'z']
''')

check_program('''x = 3
__doc__ = 'outer'
class C:
    print('later' in locals(), __doc__)
    saved = locals()
    later = 4
    saved['added'] = 5
    del later
    print('later' in saved)
print(C.added, C.__doc__)
class D:
    'class documentation'
    print(__doc__)
print(D.__doc__)
''',
              '''False outer
False
5 None
class documentation
class documentation
''')

check_program('''def outer():
    class C:
        def method(self): pass
    return C
C = outer()
print(C.__qualname__, C.method.__qualname__)
''',
              '''outer.<locals>.C outer.<locals>.C.method
''')

check_program('''events = []
class A:
    def __matmul__(self, other):
        events.append('left')
        return NotImplemented
    def __rmatmul__(self, other):
        events.append('base reflected')
        return 3
class B(A):
    def __rmatmul__(self, other):
        events.append('derived reflected')
        return 4
class C:
    def __rmatmul__(self, other): return 5
    def __imatmul__(self, other): return 6
print(A() @ B(), events)
events = []
print(A() @ C(), events)
c = C()
c @= A()
print(c)
a = A()
a @= B()
print(a)
''',
              '''4 ['derived reflected']
5 ['left']
6
4
''')

check_program('''class C:
    def __complex__(self): return 1+2j
class F:
    def __float__(self): return 3.5
class I:
    def __index__(self): return 4
print(complex(C()), complex(F()), complex(I()))
z = 3+4j
print(complex(z) is z, {1+0j: 3}[1], 9007199254740992+0j == 9007199254740993)
''',
              '''(1+2j) (3.5+0j) (4+0j)
True 3 False
''')

check_program('''# type.__subclasses__ lists live direct subclasses in creation order.
class A: pass
class B(A): pass
class C(A): pass
class D(B, C): pass
print(A.__subclasses__(), B.__subclasses__(), D.__subclasses__())
del C
print([k.__name__ for k in A.__subclasses__()])
print(bool in int.__subclasses__())
''',
              '''[<class '__main__.B'>, <class '__main__.C'>] [<class '__main__.D'>] []
['B', 'C']
True
''')

check_program('''class U:
    def __init__(self): self.data = {}
    def __repr__(self): return repr(self.data)
d = U(); d.data[1] = d
print(repr(d))
l = []; l.append(l); print(l)
class L:
    def __init__(self): self.data = []
    def __repr__(self): return repr(self.data)
x = L(); x.data.append(x); print(repr(x))
''',
              '''{1: {...}}
[[...]]
[[...]]
''')

check_program('''class A:
    def __aiter__(self): return []
aiter(A())
''',
              '''TypeError: A.__aiter__() must return an async iterator, not list
''')

check_program('''class A:
    def __anext__(self): return 1
next(anext(A(), 2))
''',
              '''TypeError: 'int' object can't be awaited
''')

check_program('''class C:
    def __complex__(self): return 1
complex(C())
''',
              '''TypeError: C.__complex__() must return a complex, not int
''')
