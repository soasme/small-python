# spec: PLS-315 16.4, 20.2
# description: Programs on class creation: namespaces and metaclasses, each with the output CPython 3.15 gives.
from harness import *

check_program('''
events = []
class Namespace(dict):
    def __getitem__(self, key):
        events.append(('get', key))
        return dict.__getitem__(self, key)
    def __setitem__(self, key, value):
        events.append(('set', key))
        dict.__setitem__(self, key, value)
    def __delitem__(self, key):
        events.append(('del', key))
        dict.__delitem__(self, key)
namespace = Namespace()
class Meta(type):
    @classmethod
    def __prepare__(meta, name, bases): return namespace
    def __new__(meta, name, bases, ns):
        print(ns is namespace)
        return type.__new__(meta, name, bases, ns)
fallback = 'global'
def outer():
    fallback = 'closure'
    class C(metaclass=Meta):
        before = fallback
        fallback = 'local'
        after = fallback
        same = locals() is namespace
        temporary = 42
        del temporary
        try: del missing
        except NameError: pass
    return C
C = outer()
print(C.before, C.after, C.same, 'temporary' in C.__dict__)
print(events)
namespace.clear()
events.clear()
exec('x = 41; y = x + 1; del x', {}, namespace)
print(dict(namespace), events)
events.clear()
print(eval('y + 1', {}, namespace), events)
events.clear()
print(eval('dir()', {}, namespace), events)
class Missing(dict):
    def __missing__(self, name): return ('missing', name)
print(eval('whatever', {}, Missing()))
''',
              '''True
global local True False
[('get', '__name__'), ('set', '__module__'), ('set', '__qualname__'), ('set', '__firstlineno__'), ('get', 'fallback'), ('set', 'before'), ('set', 'fallback'), ('get', 'fallback'), ('set', 'after'), ('get', 'locals'), ('get', 'namespace'), ('set', 'same'), ('set', 'temporary'), ('del', 'temporary'), ('del', 'missing'), ('get', 'NameError'), ('set', '__static_attributes__')]
{'y': 42} [('set', 'x'), ('get', 'x'), ('set', 'y'), ('del', 'x')]
43 [('get', 'y')]
['y'] [('get', 'dir')]
('missing', 'whatever')
''')

check_program('''
events = []
class Namespace:
    def __init__(self): self.data = {}
    def __getitem__(self, key):
        events.append(('get', key))
        return self.data[key]
    def __setitem__(self, key, value):
        events.append(('set', key))
        self.data[key] = value
    def __delitem__(self, key):
        events.append(('del', key))
        del self.data[key]
    def keys(self): return self.data.keys()
namespace = Namespace()
def meta(name, bases, ns):
    print(ns is namespace)
    return type(name, bases, dict(ns))
def prepare(name, bases): return namespace
meta.__prepare__ = prepare
class C(metaclass=meta):
    a = 3
    b = a + 4
    del a
    same = locals() is namespace
print(C.b, C.same, events)
events.clear()
exec('a = 1; b = a + 2; del a', {}, namespace)
print(namespace.data['b'], events)
print(eval('locals()', {}, namespace) is namespace)
print(eval('dir()', {}, namespace))
class ReadOnly:
    def __getitem__(self, key):
        if key == 'answer': return 42
        raise KeyError(key)
print(eval('answer + len(())', {}, ReadOnly()))
for source in ['x', 'del x']:
    try: exec(source, {}, Namespace())
    except NameError: print('missing name')
class Exploding(Namespace):
    def __getitem__(self, key): raise ValueError('lookup')
try: eval('x', {}, Exploding())
except ValueError as error: print(error)
class Broken(Namespace):
    def __setitem__(self, key, value): raise ValueError('store')
try: exec('x = 1', {}, Broken())
except ValueError as error: print(error)
class BrokenDelete(Namespace):
    def __delitem__(self, key): raise ValueError('delete')
try: exec('del x', {}, BrokenDelete())
except NameError: print('delete failure becomes missing name')
''',
              '''True
7 True [('get', '__name__'), ('set', '__module__'), ('set', '__qualname__'), ('set', '__firstlineno__'), ('set', 'a'), ('get', 'a'), ('set', 'b'), ('del', 'a'), ('get', 'locals'), ('get', 'namespace'), ('set', 'same'), ('set', '__static_attributes__'), ('get', '__module__'), ('get', '__qualname__'), ('get', '__firstlineno__'), ('get', 'b'), ('get', 'same'), ('get', '__static_attributes__')]
3 [('set', 'a'), ('get', 'a'), ('set', 'b'), ('del', 'a')]
True
['__firstlineno__', '__module__', '__qualname__', '__static_attributes__', 'b', 'same']
42
missing name
missing name
lookup
store
delete failure becomes missing name
''')

check_program('''
class Globals(dict):
    def __getitem__(self, key):
        print('global read', key)
        return dict.__getitem__(self, key)
    def __setitem__(self, key, value): raise AssertionError('global write hook')
    def __delitem__(self, key): raise AssertionError('global delete hook')
namespace = Globals()
local = {}
exec('global x; x = 3', namespace, local)
exec('def f(): return x', namespace, local)
print(local['f']())
print(local['f'].__globals__ is namespace)
exec('global x; del x', namespace, local)
print('x' in namespace)
class C:
    def method(self):
        self.z = self.a = 1
        self.__private = 2
        self.ignored: int
        self.typed: int = 4
        del self.deleted
        other.field = 3
        self.z += 1
        def nested(): self.nested = 3
        class D:
            self.from_nested_body = 5
            def method(self): self.inside = 3
        return D
    def second(this): this.excluded = 2
print(C.__static_attributes__)
class Dead:
    def method(self):
        if False: self.dead = 1
        for self.loop in []: pass
        with context as self.manager: pass
        self.unpack, *self.star = []
print(Dead.__static_attributes__)
''',
              '''global read x
3
True
False
('__private', 'a', 'from_nested_body', 'nested', 'typed', 'z')
('dead', 'loop', 'manager', 'star', 'unpack')
''')

check_program('''
class Extra:
    value = 13
class Meta(type):
    def mro(cls):
        print(cls.__name__, cls.__mro__, [c.__name__ for c in cls.__bases__])
        return [cls, Extra, object]
class C(metaclass=Meta): pass
print(C.value, issubclass(C, Extra))
Extra.value = 17
print(C.value)
print([c.__name__ for c in type.mro(C)])
class X: pass
class Y: pass
class XY(X, Y): pass
class YX(Y, X): pass
class Resolved(XY, YX, metaclass=Meta): pass
print([c.__name__ for c in Resolved.__mro__])
class Reverse(type):
    def mro(cls):
        order = super().mro()
        return order[:1] + list(reversed(order[1:-1])) + order[-1:]
class D(X, Y, metaclass=Reverse): pass
print([c.__name__ for c in D.__mro__])
print([c.__name__ for c in type.mro(D)])
class Iterated(type):
    def mro(cls): return iter([cls, object])
class E(metaclass=Iterated): pass
print([c.__name__ for c in E.__mro__])
for order in [[], [1], [str], [Exception]]:
    class Invalid(type):
        def mro(cls): return order
    try:
        class F(metaclass=Invalid): pass
    except TypeError as error: print(type(error).__name__)
class Raising(type):
    def mro(cls): raise ValueError('mro failure')
try:
    class F(metaclass=Raising): pass
except ValueError as error: print(error)
''',
              '''C None ['object']
13 True
17
['C', 'object']
Resolved None ['XY', 'YX']
['Resolved', 'Extra', 'object']
['D', 'Y', 'X', 'object']
['D', 'X', 'Y', 'object']
['E', 'object']
TypeError
TypeError
TypeError
TypeError
mro failure
''')

check_program('''
events = []
class Descriptor:
    def __set_name__(self, owner, name):
        events.append(('name', owner.__name__, name))
        if name == 'first':
            del owner.second
            owner.third = Descriptor()
    def __get__(self, instance, owner):
        return (instance is None, owner.__name__)
class Base:
    def __init_subclass__(cls, *, x, **kwargs):
        events.append(('init', cls.__name__, x, kwargs))
        super().__init_subclass__(**kwargs)
def decorate(cls):
    events.append(('decorate', cls.__name__))
    return cls
@decorate
class Child(Base, x=3):
    first = Descriptor()
    second = Descriptor()
print(events)
print(Child.first, Child().first)
class Grandchild(Child, x=4): pass
print(events)
class Broken:
    def __set_name__(self, owner, name): raise ValueError('broken')
try:
    class Failed:
        attr = Broken()
except ValueError as error:
    print(str(error), error.__notes__)
class NoHook:
    def __getattr__(self, name): raise AssertionError(name)
class Quiet:
    value = NoHook()
error = ValueError('message')
error.add_note('first')
error.add_note('second')
print(error.__notes__)
for value in [1, None, []]:
    try: error.add_note(value)
    except TypeError: print('invalid note')
error.__notes__ = ()
try: error.add_note('third')
except TypeError: print('invalid note list')
''',
              '''[('name', 'Child', 'first'), ('name', 'Child', 'second'), ('init', 'Child', 3, {}), ('decorate', 'Child')]
(True, 'Child') (False, 'Child')
[('name', 'Child', 'first'), ('name', 'Child', 'second'), ('init', 'Child', 3, {}), ('decorate', 'Child'), ('init', 'Grandchild', 4, {})]
broken ["Error calling __set_name__ on 'Broken' instance 'attr' in 'Failed'"]
['first', 'second']
invalid note
invalid note
invalid note
invalid note list
''')

check_program('''
class Base:
    def method(self): return ['Base']
    @classmethod
    def cm(cls): return [cls.__name__]
    @staticmethod
    def sm(): return 'static'
    @property
    def prop(self): return self.__class__.__name__
class Left(Base):
    def method(self): return ['Left'] + super().method()
    @classmethod
    def cm(cls): return ['Left'] + super().cm()
class Right(Base):
    right_only = 1
    def method(self): return ['Right'] + super().method()
    @classmethod
    def cm(cls): return ['Right'] + super().cm()
class Diamond(Left, Right):
    def nested(self):
        def read_class(): return __class__
        return read_class()
    def generator(self):
        yield super().method()
        yield __class__.__name__
value = Diamond()
print(value.method(), Diamond.cm(), Diamond.sm(), value.prop)
print(value.nested() is Diamond, list(value.generator()))
print([cls.__name__ for cls in Diamond.__mro__])
print(Diamond.mro() == list(Diamond.__mro__), Diamond.__bases__ == (Left, Right))
print(type.mro(Diamond) == Diamond.mro())
print('right_only' in dir(Diamond), 'right_only' in dir(value))
print(super(Left, value).method(), super(Right, value).method())
unbound = super(Left)
print(unbound.__self__, unbound.__self_class__, unbound.__thisclass__ is Left)
bound = unbound.__get__(value, Diamond)
print(bound.method(), bound.__self__ is value, bound.__self_class__ is Diamond)
print(bound.__get__(value) is bound, unbound.__get__(None, Diamond) is unbound)
class WithSuper(Left):
    proxy = super(Left)
print(WithSuper().proxy.method(), WithSuper.proxy.__self__)
for args in [(1,), (Left, 1), (Left, Base()), (Left, Right)]:
    try: super(*args)
    except TypeError: print('invalid super arguments')
class Cell:
    def change(self, value):
        nonlocal __class__
        __class__ = value
    def read(self): return __class__
obj = Cell()
print(obj.read() is Cell)
obj.change(Base)
print(obj.read() is Base)
class Shadow(Base):
    __class__ = 413
    def method(self): return super().method()
print(Shadow().method(), Shadow().__class__)
class Proxy:
    @property
    def __class__(self): return Diamond
proxy = Proxy()
print(super(Left, proxy).method())
def outside(self):
    try: super()
    except RuntimeError as error: print(error)
outside(value)
class Local:
    def method(self):
        __class__ = Base
        try: super()
        except RuntimeError as error: print(error)
    def deleted(self):
        del self
        try: super()
        except RuntimeError as error: print(error)
Local().method()
Local().deleted()
''',
              '''['Left', 'Right', 'Base'] ['Left', 'Right', 'Diamond'] static Diamond
True [['Left', 'Right', 'Base'], 'Diamond']
['Diamond', 'Left', 'Right', 'Base', 'object']
True True
True
True True
['Right', 'Base'] ['Base']
None None True
['Right', 'Base'] True True
True True
['Base'] None
invalid super arguments
invalid super arguments
invalid super arguments
invalid super arguments
True
True
['Base'] 413
['Right', 'Base']
super(): __class__ cell not found
super(): __class__ cell not found
super(): arg[0] deleted
''')

check_program('''
events = []
def marked(tag, value):
    events.append(tag)
    return value
class Base:
    def __init_subclass__(cls, **kwargs): cls.kwargs = kwargs
class Child(marked('base', Base), x=marked('x', 1), *marked('star', ()), **marked('map', {'y': 2})): pass
print(events, Child.kwargs)
class Root:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.calls = []
class Left(Root): pass
class Middle:
    def __init_subclass__(cls, middle, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.calls += [middle]
class Right(Root):
    def __init_subclass__(cls, right='right', **kwargs):
        super().__init_subclass__(**kwargs)
        cls.calls += [right]
class Diamond(Left, Middle, Right, middle='middle'): pass
print(Diamond.calls, Left.calls, Right.calls)
T = type('Dynamic', (Base,), {'a': 3}, x=4)
print(T.__name__, T.__qualname__, T.__module__, T.a, T.kwargs)
print(type('Empty', (), {}).__bases__ == (object,))
class Generic:
    def __class_getitem__(cls, key): return cls.__name__, key
class ChildGeneric(Generic): pass
print(Generic[int], ChildGeneric[1, 2], Generic.__class_getitem__('direct'))
class Disabled(Generic): __class_getitem__ = None
try: Disabled[1]
except TypeError as error: print(error)
class Static:
    @staticmethod
    def __class_getitem__(key): return key
print(Static[1])
prop = property(lambda self: 42)
print(prop.__name__)
class Owner: renamed = prop
print(prop.__name__)
copied = prop.setter(lambda self, value: None)
print(copied.__name__)
del copied.__name__
print(copied.__name__)
prop.__name__ = ['arbitrary']
print(prop.__name__)
prop.__set_name__(None, 'manual')
print(prop.__name__)
class A: pass
class B: pass
class AB(A, B): pass
class BA(B, A): pass
for bases in [(A,A), (AB,BA), (object,A), (1,)]:
    try: type('Bad', bases, {})
    except TypeError: print('invalid bases')
''',
              '''['base', 'star', 'x', 'map'] {'x': 1, 'y': 2}
['right', 'middle'] [] []
Dynamic Dynamic __main__ 3 {'x': 4}
True
('Generic', <class 'int'>) ('ChildGeneric', (1, 2)) ('Generic', 'direct')
type 'Disabled' is not subscriptable
1
<lambda>
renamed
renamed
<lambda>
['arbitrary']
manual
invalid bases
invalid bases
invalid bases
invalid bases
''')

check_program('''classes = [object]
try:
    value = type("C0", (classes[0],), {})
    print([cls.__name__ for cls in value.__mro__])
except TypeError:
    value = object
    print("inconsistent")
classes.append(value)
try:
    value = type("C17", (classes[14], classes[10], classes[13], classes[8],), {})
    print([cls.__name__ for cls in value.__mro__])
except TypeError:
    value = object
    print("inconsistent")
classes.append(value)
try:
    value = type("C34", (classes[8], classes[6], classes[1],), {})
    print([cls.__name__ for cls in value.__mro__])
except TypeError:
    value = object
    print("inconsistent")
classes.append(value)
try:
    value = type("C51", (classes[42],), {})
    print([cls.__name__ for cls in value.__mro__])
except TypeError:
    value = object
    print("inconsistent")
classes.append(value)
try:
    value = type("C68", (classes[41], classes[38], classes[36],), {})
    print([cls.__name__ for cls in value.__mro__])
except TypeError:
    value = object
    print("inconsistent")
classes.append(value)
try:
    value = type("C85", (classes[56], classes[60], classes[85],), {})
    print([cls.__name__ for cls in value.__mro__])
except TypeError:
    value = object
    print("inconsistent")
classes.append(value)
try:
    value = type("C102", (classes[61], classes[59], classes[61],), {})
    print([cls.__name__ for cls in value.__mro__])
except TypeError:
    value = object
    print("inconsistent")
classes.append(value)
try:
    value = type("C119", (classes[14], classes[29],), {})
    print([cls.__name__ for cls in value.__mro__])
except TypeError:
    value = object
    print("inconsistent")
classes.append(value)
try:
    value = type("C136", (classes[1],), {})
    print([cls.__name__ for cls in value.__mro__])
except TypeError:
    value = object
    print("inconsistent")
classes.append(value)
try:
    value = type("C153", (classes[10],), {})
    print([cls.__name__ for cls in value.__mro__])
except TypeError:
    value = object
    print("inconsistent")
classes.append(value)
try:
    value = type("C170", (classes[96],), {})
    print([cls.__name__ for cls in value.__mro__])
except TypeError:
    value = object
    print("inconsistent")
classes.append(value)
try:
    value = type("C187", (classes[122],), {})
    print([cls.__name__ for cls in value.__mro__])
except TypeError:
    value = object
    print("inconsistent")
classes.append(value)
try:
    value = type("C204", (classes[19], classes[152], classes[66], classes[130],), {})
    print([cls.__name__ for cls in value.__mro__])
except TypeError:
    value = object
    print("inconsistent")
classes.append(value)
try:
    value = type("C221", (classes[34], classes[150], classes[84], classes[60],), {})
    print([cls.__name__ for cls in value.__mro__])
except TypeError:
    value = object
    print("inconsistent")
classes.append(value)
try:
    value = type("C238", (classes[118], classes[129], classes[179],), {})
    print([cls.__name__ for cls in value.__mro__])
except TypeError:
    value = object
    print("inconsistent")
''',
              '''['C0', 'object']
IndexError: list index out of range
''')

check_program('''
events = []
class Data:
    def __get__(self, obj, owner):
        events.append(('descriptor get', owner.__name__))
        return object.__getattribute__(obj, '_value')
    def __set__(self, obj, value):
        events.append(('descriptor set', value))
        object.__setattr__(obj, '_value', value)
    def __delete__(self, obj):
        events.append('descriptor delete')
        object.__delattr__(obj, '_value')
class Base:
    value = Data()
    def __getattribute__(self, name):
        events.append(('get', name))
        if name == 'virtual': return 42
        return super().__getattribute__(name)
    def __getattr__(self, name):
        events.append(('fallback', name))
        return 'absent'
    def __setattr__(self, name, value):
        events.append(('set', name, value))
        return super().__setattr__(name, value)
    def __delattr__(self, name):
        events.append(('delete', name))
        return super().__delattr__(name)
    def __len__(self): return 4
    def __hash__(self): return 5
class Child(Base): pass
value = Child()
value.value = 3
print(value.value, value.virtual, value.missing)
del value.value
print(value.value, len(value), hash(value))
print(events)
events.clear()
object.__setattr__(value, 'direct', 7)
print(object.__getattribute__(value, 'direct'))
object.__delattr__(value, 'direct')
print(events)
try: object.__getattribute__(value, 'missing')
except AttributeError: print('direct lookup has no fallback')
def replace(self, name): return 'replaced'
Child.__getattribute__ = replace
print(value.anything)
del Child.__getattribute__
print(value.virtual)
class Bind:
    def __get__(self, obj, owner): return lambda name: (name, owner.__name__)
class Special:
    __getattribute__ = Bind()
print(Special().custom)
class Broken:
    def __getattribute__(self, name): raise ValueError(name)
    def __getattr__(self, name): raise AssertionError('must not run')
try: Broken().name
except ValueError as error: print(error)
class Recurse:
    def __getattribute__(self, name): return self.value
try: Recurse().value
except RecursionError: print('recursive lookup bounded')
for operation in [lambda: object.__setattr__(str, 'x', 1), lambda: object.__delattr__(str, 'x')]:
    try: operation()
    except TypeError: print('cannot bypass type attribute rules')
''',
              '''3 42 absent
absent 4 5
[('set', 'value', 3), ('descriptor set', 3), ('get', 'value'), ('descriptor get', 'Child'), ('get', 'virtual'), ('get', 'missing'), ('fallback', 'missing'), ('delete', 'value'), 'descriptor delete', ('get', 'value'), ('descriptor get', 'Child'), ('fallback', 'value')]
7
[]
direct lookup has no fallback
replaced
42
('custom', 'Special')
name
recursive lookup bounded
cannot bypass type attribute rules
cannot bypass type attribute rules
''')
