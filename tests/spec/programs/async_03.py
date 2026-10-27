# spec: PLS-315 27.3, 27.5
# description: Programs on asynchronous generator operation states, each with the output CPython 3.15 gives.
from harness import *

check_program('''
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
drive(g.__anext__(), 'next')
op = g.asend(7)
drive(op, 'next')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent 7
result waiting
error StopIteration ('resumed',)
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.asend(7)
drive(op, 'send')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent 42
result waiting
error StopIteration ('resumed',)
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.asend(7)
drive(op, 'throw')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
error StopIteration ('caught generator',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.asend(7)
drive(op, 'exit')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
result waiting
cleanup
error GeneratorExit ()
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.asend(7)
drive(op, 'close')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
error RuntimeError ('coroutine ignored GeneratorExit',)
cleanup
error GeneratorExit ()
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.athrow(ValueError)
drive(op, 'next')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
error StopIteration ('caught generator',)
error RuntimeError ('cannot reuse already awaited aclose()/athrow()',)
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.athrow(ValueError)
drive(op, 'send')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
error RuntimeError ("can't send non-None value to a just-started coroutine",)
error StopIteration ('caught generator',)
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.athrow(ValueError)
drive(op, 'throw')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
error StopIteration ('caught generator',)
error RuntimeError ('cannot reuse already awaited aclose()/athrow()',)
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.athrow(ValueError)
drive(op, 'exit')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
result waiting
cleanup
error GeneratorExit ()
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.athrow(ValueError)
drive(op, 'close')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
error RuntimeError ('coroutine ignored GeneratorExit',)
cleanup
error GeneratorExit ()
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.athrow(GeneratorExit)
drive(op, 'next')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
result waiting
cleanup
error GeneratorExit ()
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.athrow(GeneratorExit)
drive(op, 'send')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
error RuntimeError ("can't send non-None value to a just-started coroutine",)
result waiting
running True
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.athrow(GeneratorExit)
drive(op, 'throw')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
error StopIteration ('caught generator',)
error RuntimeError ('cannot reuse already awaited aclose()/athrow()',)
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.athrow(GeneratorExit)
drive(op, 'exit')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
result waiting
cleanup
error GeneratorExit ()
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.athrow(GeneratorExit)
drive(op, 'close')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
error RuntimeError ('coroutine ignored GeneratorExit',)
cleanup
error GeneratorExit ()
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.aclose()
drive(op, 'next')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
result waiting
cleanup
error StopIteration ()
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.aclose()
drive(op, 'send')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
error RuntimeError ("can't send non-None value to a just-started coroutine",)
result waiting
running True
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.aclose()
drive(op, 'throw')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
error RuntimeError ('async generator ignored GeneratorExit',)
error RuntimeError ('cannot reuse already awaited aclose()/athrow()',)
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.aclose()
drive(op, 'exit')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
result waiting
cleanup
error StopIteration ()
running False
''')

check_program('''
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
drive(g.__anext__(), 'next')
op = g.aclose()
drive(op, 'close')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
error RuntimeError ('coroutine ignored GeneratorExit',)
cleanup
error StopIteration ()
running False
''')
