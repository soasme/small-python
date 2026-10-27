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
op = g.__anext__()
drive(op, 'next')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
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
op = g.__anext__()
drive(op, 'send')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error TypeError ("can't send non-None value to a just-started async generator",)
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
op = g.__anext__()
drive(op, 'throw')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error ValueError ('injected',)
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
op = g.__anext__()
drive(op, 'exit')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error GeneratorExit ()
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
op = g.__anext__()
drive(op, 'close')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''result None
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
op = g.asend(None)
drive(op, 'next')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error StopIteration ('first',)
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
op = g.asend(None)
drive(op, 'send')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error TypeError ("can't send non-None value to a just-started async generator",)
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
op = g.asend(None)
drive(op, 'throw')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error ValueError ('injected',)
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
op = g.asend(None)
drive(op, 'exit')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error GeneratorExit ()
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
op = g.asend(None)
drive(op, 'close')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''result None
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
op = g.asend(7)
drive(op, 'next')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error TypeError ("can't send non-None value to a just-started async generator",)
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
op = g.asend(7)
drive(op, 'send')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error TypeError ("can't send non-None value to a just-started async generator",)
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
op = g.asend(7)
drive(op, 'throw')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error ValueError ('injected',)
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
op = g.asend(7)
drive(op, 'exit')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error GeneratorExit ()
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
op = g.asend(7)
drive(op, 'close')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''result None
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
op = g.athrow(ValueError)
drive(op, 'next')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error ValueError ()
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
op = g.athrow(ValueError)
drive(op, 'send')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error RuntimeError ("can't send non-None value to a just-started coroutine",)
error ValueError ()
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
op = g.athrow(ValueError)
drive(op, 'throw')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error ValueError ('injected',)
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
op = g.athrow(ValueError)
drive(op, 'exit')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''error GeneratorExit ()
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
op = g.athrow(ValueError)
drive(op, 'close')
drive(op, 'next')
print('running', g.ag_running)
''',
              '''result None
error RuntimeError ('cannot reuse already awaited aclose()/athrow()',)
running False
''')
