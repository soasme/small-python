# spec: PLS-315 16.5
# description: Programs on decorators, each with the output CPython 3.15 gives.
from harness import *

check_program('''# Factory behavior exercised by CPython test_descr.test_funny_new.
class C:
    def __new__(cls, arg):
        if isinstance(arg, str): return [1, 2, 3]
        if isinstance(arg, int): return object.__new__(D)
        return object.__new__(cls)
class D(C):
    def __init__(self, arg): self.foo = arg
print(C('1'), D('1'), D(None).foo, C(1).foo, D(1).foo)
print(type(C(1)) is D)
class Static:
    @staticmethod
    def __new__(*args): return args
class DerivedStatic(Static): pass
print(Static(1, 2) == (Static, 1, 2), DerivedStatic(1, 2) == (DerivedStatic, 1, 2))
class Class:
    @classmethod
    def __new__(*args): return args
class DerivedClass(Class): pass
print(Class(1, 2) == (Class, Class, 1, 2), DerivedClass(1, 2) == (DerivedClass, DerivedClass, 1, 2))
class Plain:
    def __new__(cls, value=0):
        result = object.__new__(cls)
        result.value = value
        return result
p = Plain(value=42)
print(p.value, Plain.__new__(Plain, 3).value, p.__new__(Plain, 4).value)
''',
              '''[1, 2, 3] [1, 2, 3] None 1 1
True
True True
True True
42 3 4
''')

check_program('''events = []
def decorator(label):
    events.append(('evaluate', label))
    def apply(fn):
        events.append(('apply', label))
        return fn
    return apply
def default():
    events.append('default')
    return 17
@decorator('outer')
@decorator('inner')
def f(x=default()):
    return x
@decorator('class')
class C:
    events.append('body')
print(events, f(), C.__name__)
''',
              '''[('evaluate', 'outer'), ('evaluate', 'inner'), 'default', ('apply', 'inner'), ('apply', 'outer'), ('evaluate', 'class'), 'body', ('apply', 'class')] 17 C
''')

check_program('''@1
def f(): pass
''',
              '''TypeError: 'int' object is not callable
''')
