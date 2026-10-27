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
owner = g.asend(None)
drive(owner, 'next')
op = g.__anext__()
drive(op, 'next')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('anext(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.__anext__()
drive(op, 'send')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('anext(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.__anext__()
drive(op, 'throw')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('anext(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.__anext__()
drive(op, 'exit')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('anext(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.__anext__()
drive(op, 'close')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('anext(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.asend(None)
drive(op, 'next')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('anext(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.asend(None)
drive(op, 'send')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('anext(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.asend(None)
drive(op, 'throw')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('anext(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.asend(None)
drive(op, 'exit')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('anext(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.asend(None)
drive(op, 'close')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('anext(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.asend(7)
drive(op, 'next')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('anext(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.asend(7)
drive(op, 'send')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('anext(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.asend(7)
drive(op, 'throw')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('anext(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.asend(7)
drive(op, 'exit')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('anext(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.asend(7)
drive(op, 'close')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('anext(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited __anext__()/asend()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.athrow(ValueError)
drive(op, 'next')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('athrow(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited aclose()/athrow()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.athrow(ValueError)
drive(op, 'send')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('athrow(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited aclose()/athrow()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.athrow(ValueError)
drive(op, 'throw')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('athrow(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited aclose()/athrow()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.athrow(ValueError)
drive(op, 'exit')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('athrow(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited aclose()/athrow()',)
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
owner = g.asend(None)
drive(owner, 'next')
op = g.athrow(ValueError)
drive(op, 'close')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
sent None
result waiting
error RuntimeError ('athrow(): asynchronous generator is already running',)
error RuntimeError ('cannot reuse already awaited aclose()/athrow()',)
running True
''')
