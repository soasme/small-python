# spec: PLS-315 27.4
# description: Programs on coroutines, each with the output CPython 3.15 gives.
from harness import *

check_program('''async def f():
    return lambda: await x
''',
              '''SyntaxError: 'await' outside async function (<program>, line 2)
''')

check_program('''async def f():
    return await -1
''',
              '''SyntaxError: invalid syntax (<program>, line 2)
''')

check_program('''async def f():
    return await 1
f().send(None)
''',
              '''TypeError: 'int' object can't be awaited
''')

check_program('''class A:
    def __await__(self): return [1]
async def f():
    return await A()
f().send(None)
''',
              '''TypeError: A.__await__() must return an iterator, not list
''')

check_program('''async def f():
    async for x in []:
        pass
f().send(None)
''',
              '''TypeError: 'async for' requires an object with __aiter__ method, got list
''')

check_program('''class A:
    def __aiter__(self): return self
    def __anext__(self): return 1
async def f():
    async for x in A(): pass
f().send(None)
''',
              '''TypeError: 'async for' received an invalid object from __anext__: int
''')
