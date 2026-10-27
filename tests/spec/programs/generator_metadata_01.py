# spec: PLS-315 27.2, 27.4, 27.5
# description: Programs on generator, coroutine and async generator names and states, each with the output CPython 3.15 gives.
from harness import *

check_program('''
class Name(str): pass
def factory():
    def gen(): yield 1
    async def coro(): return 2
    async def agen(): yield 3
    return gen, coro, agen
for make in factory():
    old = make()
    make.__name__ = 'renamed'
    make.__qualname__ = 'qualified.renamed'
    new = make()
    print(old.__name__, old.__qualname__, new.__name__, new.__qualname__)
    print(repr(old).split(' at ')[0], repr(new).split(' at ')[0])
    for field in ['__name__', '__qualname__']:
        text = Name('changed')
        setattr(new, field, text)
        print(field, getattr(new, field) is text)
        for value in [None, 17, [], object()]:
            try: setattr(new, field, value)
            except TypeError as error: print(str(error))
        try: delattr(new, field)
        except TypeError as error: print(str(error))
    if hasattr(new, 'close'):
        old.close()
        new.close()
    print(new.__name__, new.__qualname__)
''',
              '''gen factory.<locals>.gen renamed qualified.renamed
<generator object factory.<locals>.gen <generator object qualified.renamed
__name__ True
__name__ must be set to a string object
__name__ must be set to a string object
__name__ must be set to a string object
__name__ must be set to a string object
__name__ must be set to a string object
__qualname__ True
__qualname__ must be set to a string object
__qualname__ must be set to a string object
__qualname__ must be set to a string object
__qualname__ must be set to a string object
__qualname__ must be set to a string object
changed changed
coro factory.<locals>.coro renamed qualified.renamed
<coroutine object factory.<locals>.coro <coroutine object qualified.renamed
__name__ True
__name__ must be set to a string object
__name__ must be set to a string object
__name__ must be set to a string object
__name__ must be set to a string object
__name__ must be set to a string object
__qualname__ True
__qualname__ must be set to a string object
__qualname__ must be set to a string object
__qualname__ must be set to a string object
__qualname__ must be set to a string object
__qualname__ must be set to a string object
changed changed
agen factory.<locals>.agen renamed qualified.renamed
<async_generator object factory.<locals>.agen <async_generator object qualified.renamed
__name__ True
__name__ must be set to a string object
__name__ must be set to a string object
__name__ must be set to a string object
__name__ must be set to a string object
__name__ must be set to a string object
__qualname__ True
__qualname__ must be set to a string object
__qualname__ must be set to a string object
__qualname__ must be set to a string object
__qualname__ must be set to a string object
__qualname__ must be set to a string object
changed changed
''')

check_program('''
def show(g, prefix):
    print(getattr(g, prefix + '_state'), getattr(g, prefix + '_running'), getattr(g, prefix + '_suspended'))
def gen():
    show(g, 'gi')
    yield 1
    show(g, 'gi')
g = gen()
show(g, 'gi')
next(g)
show(g, 'gi')
next(g, None)
show(g, 'gi')
class Pause:
    def __await__(self):
        yield 'pause'
async def coro():
    show(c, 'cr')
    await Pause()
    show(c, 'cr')
c = coro()
show(c, 'cr')
c.send(None)
show(c, 'cr')
try: c.send(None)
except StopIteration: pass
show(c, 'cr')
async def agen():
    show(a, 'ag')
    yield 1
    await Pause()
    show(a, 'ag')
a = agen()
show(a, 'ag')
for i in range(3):
    op = a.__anext__()
    try: print(op.send(None))
    except (StopIteration, StopAsyncIteration): pass
    show(a, 'ag')
    if a.ag_running:
        try: op.send(None)
        except StopAsyncIteration: pass
        show(a, 'ag')
''',
              '''GEN_CREATED False False
GEN_RUNNING True False
GEN_SUSPENDED False True
GEN_RUNNING True False
GEN_CLOSED False False
CORO_CREATED False False
CORO_RUNNING True False
CORO_SUSPENDED False True
CORO_RUNNING True False
CORO_CLOSED False False
AGEN_CREATED False False
AGEN_RUNNING True False
AGEN_SUSPENDED False True
pause
AGEN_SUSPENDED True True
AGEN_RUNNING True False
AGEN_CLOSED False False
AGEN_CLOSED False False
''')
