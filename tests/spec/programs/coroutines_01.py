# spec: PLS-315 27.4
# description: Programs on coroutines, each with the output CPython 3.15 gives.
from harness import *

check_program('''class Manager:
    def __enter__(self): print('enter'); return 42
    def __exit__(self, kind, value, tb): print('exit')
with (Manager() as a, Manager() as b,): print(a + b)
with (Manager()) as a: print(a)
class AsyncManager:
    async def __aenter__(self): print('aenter'); return 3
    async def __aexit__(self, kind, value, tb): print('aexit')
async def run():
    async with (
        AsyncManager() as a,
        AsyncManager() as b,
    ): return a + b
try: run().send(None)
except StopIteration as error: print(error.value)
''',
              '''enter
enter
84
exit
exit
enter
42
exit
aenter
aenter
aexit
aexit
6
''')

check_program('''class BadEnter:
    def __aenter__(self): return 1
    def __aexit__(self, *args): print('wrong exit')
class BadExit:
    async def __aenter__(self): return self
    def __aexit__(self, *args): return 1
async def run(manager):
    async with manager:
        raise ValueError('body')
for manager in [BadEnter(), BadExit()]:
    try: run(manager).send(None)
    except TypeError as error:
        print(error, type(error.__context__).__name__)
''',
              ''''async with' received an object from __aenter__ that does not implement __await__: int NoneType
'async with' received an object from __aexit__ that does not implement __await__: int ValueError
''')

check_program('''events = []
class Sequence:
    def __aiter__(self):
        events.append('iterator')
        self.i = 0
        return self
    async def __anext__(self):
        if self.i == 3: raise StopAsyncIteration
        self.i += 1
        return self.i
source = Sequence()
g = (x * 2 async for x in source)
print(type(g).__name__, events)
async def run():
    print([x async for x in g])
    print(events)
    async def immediate(x): return x + 1
    other = (await immediate(x) for x in range(3))
    print(type(other).__name__, [x async for x in other])
coro = run()
try: coro.send(None)
except StopIteration: print('complete')
''',
              '''async_generator ['iterator']
[2, 4, 6]
['iterator']
async_generator [1, 2, 3]
complete
''')

check_program('''events = []
class Pause:
    def __await__(self):
        events.append('pause')
        value = yield 'waiting'
        return value
async def child():
    return await Pause()
async def main():
    events.append('start')
    try:
        value = 2 + await child()
        return f'{value=}'
    finally:
        events.append('finally')
coro = main()
print(type(coro).__name__, coro.__name__, events, coro.cr_running, coro.cr_suspended)
wrapper = coro.__await__()
print(iter(wrapper) is wrapper, next(wrapper), events, coro.cr_suspended)
try:
    wrapper.send(5)
except StopIteration as error:
    print(error.value, events, coro.cr_suspended)
try:
    coro.send(None)
except RuntimeError as error:
    print(str(error))
print(coro.close())
''',
              '''coroutine main [] False False
True waiting ['start', 'pause'] True
value=7 ['start', 'pause', 'finally'] False
cannot reuse already awaited coroutine
None
''')

check_program('''class Pause:
    def __await__(self):
        try:
            yield 1
        except ValueError as error:
            print('caught', error)
            return 7
        finally:
            print('cleanup')
async def run():
    return await Pause()
coro = run(); print(coro.send(None))
try:
    coro.throw(ValueError('bad'))
except StopIteration as error:
    print(error.value)
coro = run(); print(coro.send(None)); print(coro.close())
async def immediate(value=3):
    return value
async def composed():
    return [await immediate(), await immediate(5)]
coro = composed()
try:
    coro.send(None)
except StopIteration as error:
    print(error.value)
''',
              '''1
caught bad
cleanup
7
1
cleanup
None
[3, 5]
''')

check_program('''async def f():
    raise StopIteration('escaped')
coro = f()
try:
    coro.send(None)
except RuntimeError as error:
    print(error, type(error.__cause__).__name__)
async def empty():
    pass
coro = empty()
try:
    iter(coro)
except TypeError:
    print('not iterable')
try:
    coro.send(1)
except TypeError:
    print('not started')
coro.close()
''',
              '''coroutine raised StopIteration StopIteration
not iterable
not started
''')

check_program('''class Pause:
    def __await__(self): yield 'waiting'
async def child():
    await Pause()
async def parent(value):
    return await value
value = child()
print(value.cr_await is None)
print(value.send(None), value.cr_await is not None)
other = parent(value)
try:
    other.send(None)
except RuntimeError as error:
    print(error)
value.close()
print(value.cr_await is None)
value = child(); other = parent(value)
print(other.send(None), other.cr_await is value)
other.close()
print(other.cr_await is None, value.cr_await is None)
''',
              '''True
waiting True
coroutine is being awaited already
True
waiting True
True True
''')

check_program('''events = []
class Pause:
    def __await__(self):
        yield 'step'
class Sequence:
    def __init__(self): self.index = 0
    def __aiter__(self): return self
    async def __anext__(self):
        await Pause()
        if self.index == 3: raise StopAsyncIteration
        value = self.index
        self.index += 1
        return value
async def run():
    result = []
    async for value in Sequence():
        if value == 1: continue
        result.append(value)
    else:
        events.append('complete')
    async for value in Sequence():
        result.append(value)
        break
    else:
        events.append('wrong')
    try:
        async for value in Sequence():
            raise StopAsyncIteration('body')
    except StopAsyncIteration:
        events.append('body error')
    return result
coro = run()
while True:
    try:
        print(coro.send(None))
    except StopIteration as error:
        print(error.value, events)
        break
''',
              '''step
step
step
step
step
step
[0, 2, 0] ['complete', 'body error']
''')

check_program('''events = []
class Pause:
    def __await__(self):
        try:
            yield 1
        finally:
            events.append('closed')
class Sequence:
    def __aiter__(self): return self
    async def __anext__(self): return await Pause()
async def run():
    try:
        async for value in Sequence(): pass
    finally:
        events.append('outer')
coro = run()
print(coro.send(None))
print(coro.close(), events)
''',
              '''1
None ['closed', 'outer']
''')

check_program('''class Pause:
    def __init__(self, label): self.label = label
    def __await__(self): yield self.label
class Manager:
    def __init__(self, name): self.name = name
    async def __aenter__(self):
        await Pause('enter ' + self.name)
        return self
    async def __aexit__(self, kind, value, tb):
        print('exit', self.name, kind.__name__ if kind else None)
        await Pause('exit ' + self.name)
        return self.name == 'B'
async def run():
    async with Manager('A') as a, Manager('B') as b:
        print(a.name, b.name)
        raise ValueError('body')
    for i in range(3):
        async with Manager('loop'):
            if i == 0: continue
            break
    async with Manager('return'):
        return 42
coro = run()
while True:
    try: print(coro.send(None))
    except StopIteration as error:
        print('result', error.value)
        break
''',
              '''enter A
enter B
A B
exit B ValueError
exit B
exit A None
exit A
enter loop
exit loop None
exit loop
enter loop
exit loop None
exit loop
enter return
exit return None
exit return
result 42
''')

check_program('''events = []
class Pause:
    def __await__(self): yield 'pause'
class Manager:
    async def __aenter__(self): return self
    async def __aexit__(self, kind, value, tb):
        events.append(kind.__name__ if kind else None)
        await Pause()
        return True
async def run():
    async with Manager():
        raise ValueError('first')
    return 3
coro = run(); print(coro.send(None), events)
try: coro.throw(KeyError('second'))
except KeyError as error:
    print(error, type(error.__context__).__name__, error.__context__)
coro = run(); print(coro.send(None)); print(coro.close())
async def cancelled():
    async with Manager():
        await Pause()
coro = cancelled(); print(coro.send(None))
try: coro.close()
except RuntimeError as error: print(error)
print(coro.close(), events)
''',
              '''pause ['ValueError']
'second' ValueError first
pause
None
pause
coroutine ignored GeneratorExit
None ['ValueError', 'ValueError', 'GeneratorExit']
''')

check_program('''events = []
class Manager:
    def __init__(self, name): self.name = name
    async def __aenter__(self):
        events.append(self.name)
        if self.name == 'bad': raise ValueError('entry')
        return [1]
    async def __aexit__(self, kind, value, tb):
        events.append((self.name, kind.__name__, str(value)))
async def run():
    async with Manager('outer'), Manager('bad'): pass
coro = run()
try: coro.send(None)
except ValueError as error: print(error, events)
async def unpack():
    async with Manager('unpack') as (a, b): pass
coro = unpack()
try: coro.send(None)
except ValueError as error: print(error, events[-1][0:2])
''',
              '''entry ['outer', 'bad', ('outer', 'ValueError', 'entry')]
not enough values to unpack (expected 2, got 1) ('unpack', 'ValueError')
''')

check_program('for src in ["def f[T, T](): pass", "def f[](): pass", "def f[T = int, U](): pass", "def f[*Ts: int](): pass",\n            "def f[**P: int](): pass", "type X[T, T] = int", "class C[T: (int,)]: pass", "type = 5\\nprint(type)",\n            "type X = (yield)", "def f[T: (yield)](): pass", "def f[T](x=T): pass\\nf()"]:\n    try:\n        exec(src, {})\n        print("ok", repr(src))\n    except (SyntaxError, NameError) as e:\n        print(type(e).__name__, e.msg if isinstance(e, SyntaxError) else e)\ntype = 3\nprint(type)\ndel type\nprint(type(1))\nclass A:\n    x = 1\n    type T = x\n    def m[U](self): return x\nprint(A.T.__value__)\nx = "g"\nprint(A().m())\ndef f():\n    class B[T]:\n        def g(self): return T\n    return B\nB = f()\nprint(B.__qualname__, B.g.__qualname__, B().g())\nclass K[T, *Ts, **P]: pass\nprint(K.__type_params__, K[int, str, [int]], K[int, [bytes]])\ntry: K[int]\nexcept TypeError as e: print(e)\nclass W[T = int]: pass\nprint(W[()] if False else W.__type_params__[0].__default__, W[str])\nfrom_alias = list[int] | None\nprint(from_alias, from_alias.__args__)\ntype Deep[T] = list[T] | dict[str, T]\nprint(Deep[int], Deep.__value__, Deep[int].__args__, Deep.__parameters__)\ndef gen[T](x: T) -> T:\n    yield x\nprint(next(gen(5)), gen.__type_params__)\nasync def co[T](): return 1\nprint(co.__type_params__)\nlam = [lambda: T for T in [1]]\ndef nested[T]():\n    def inner[U](): return (T, U)\n    return inner\nprint(nested()(), nested().__qualname__, nested().__type_params__)\n',
              "SyntaxError duplicate type parameter 'T'\nSyntaxError Type parameter list cannot be empty\nSyntaxError non-default type parameter 'U' follows default type parameter\nSyntaxError cannot use bound with TypeVarTuple\nSyntaxError cannot use bound with ParamSpec\nSyntaxError duplicate type parameter 'T'\nok 'class C[T: (int,)]: pass'\nok 'type = 5\\nprint(type)'\nSyntaxError yield expression cannot be used within a type alias\nSyntaxError yield expression cannot be used within a TypeVar bound\nNameError name 'T' is not defined\n3\n<class 'int'>\n1\ng\nf.<locals>.B f.<locals>.B.g T\n(T, Ts, P) __main__.K[int, str, [int]] __main__.K[int, [bytes]]\nToo few arguments for <class '__main__.K'>; actual 1, expected at least 2\n<class 'int'> __main__.W[str]\nlist[int] | None (list[int], <class 'NoneType'>)\n__main__.Deep[int] list[T] | dict[str, T] (<class 'int'>,) (T,)\n5 (T,)\n(T,)\n(T, U) nested.<locals>.inner (U,)\n")

check_program('for src in ["ub\'\'", "turf\'\'", "brft\'\'", "def foo(/,a,b=,c):\\n   pass", "def foo(a,/,/,b,c):\\n   pass",\n            "def foo(a,*b,c,/,d,e):\\n   pass", "def foo(a,*b: int=,c):\\n   pass", "def foo(a,**b: int=3):\\n   pass",\n            "def foo(a,*a, b, **c, *d):\\n   pass", "def foo(a,b,/,c,*b,c,*d,**e):\\n   pass", "def foo(a=1,/*,b,c):\\n   pass",\n            "def foo(a,d: int=,c):\\n   pass", "lambda a=1,/,**b,/,c: None", "lambda (x, y, z), w: None",\n            "def f((x, y, z, w)):\\n   pass", "def f(*): pass", "lambda *, **k: 0", "def f(a=1, b): pass",\n            "def f(a, *, a): pass", "def f(a:): pass", "def f(/): pass", "a = [1, 42 if True, 4]", "x = 1 if 1 else pass",\n            "f(]", "f(\\n]", "x = {\\n1: 2", ")", "break", "continue", "async with x: pass", "yield from x", "await x",\n            "def f(): await x", "def f(): [await x for x in y]", "break\\nx = (", "while x:\\n def f(): break",\n            "async for x in range(10):\\npass", "for x in range(10):\\n    pass\\nelse:\\npass",\n            "try:\\n    something()\\nexcept* A:\\npass", "with (A as a, B as b):\\npass", "class Blech[T](A):\\npass",\n            "match something:\\n    case []:\\n        ...\\n    case {}:\\npass", "def foo[T](x, /, y, *, z=2):\\npass"]:\n    try: compile(src, "<s>", "exec")\n    except SyntaxError as e: print(type(e).__name__, e.msg, e.lineno)\n',
              '''SyntaxError 'u' and 'b' prefixes are incompatible 1
SyntaxError 'u' and 'r' prefixes are incompatible 1
SyntaxError 'b' and 'f' prefixes are incompatible 1
SyntaxError at least one parameter must precede / 1
SyntaxError / may appear only once 1
SyntaxError / must be ahead of * 1
SyntaxError var-positional parameter cannot have default value 1
SyntaxError var-keyword parameter cannot have default value 1
SyntaxError parameters cannot follow var-keyword parameter 1
SyntaxError * may appear only once 1
SyntaxError expected comma between / and * 1
SyntaxError expected default value expression 1
SyntaxError parameters cannot follow var-keyword parameter 1
SyntaxError Lambda expression parameters cannot be parenthesized 1
SyntaxError Function parameters cannot be parenthesized 1
SyntaxError named parameters must follow bare * 1
SyntaxError named parameters must follow bare * 1
SyntaxError parameter without a default follows parameter with a default 1
SyntaxError duplicate parameter 'a' in function definition 1
SyntaxError invalid syntax 1
SyntaxError invalid syntax 1
SyntaxError expected 'else' after 'if' expression 1
SyntaxError expected expression after 'else', but statement is given 1
SyntaxError closing parenthesis ']' does not match opening parenthesis '(' 1
SyntaxError closing parenthesis ']' does not match opening parenthesis '(' on line 1 2
SyntaxError '{' was never closed 1
SyntaxError unmatched ')' 1
SyntaxError 'break' outside loop 1
SyntaxError 'continue' not properly in loop 1
SyntaxError 'async with' outside async function 1
SyntaxError 'yield from' outside function 1
SyntaxError 'await' outside function 1
SyntaxError 'await' outside async function 1
SyntaxError asynchronous comprehension outside of an asynchronous function 1
SyntaxError '(' was never closed 2
SyntaxError 'break' outside loop 2
IndentationError expected an indented block after 'for' statement on line 1 2
IndentationError expected an indented block after 'else' statement on line 3 4
IndentationError expected an indented block after 'except*' statement on line 3 4
IndentationError expected an indented block after 'with' statement on line 1 2
IndentationError expected an indented block after class definition on line 1 2
IndentationError expected an indented block after 'case' statement on line 4 5
IndentationError expected an indented block after function definition on line 1 2
''')

check_program('# CPython\'s error spans for range-based parser diagnostics and tokenizer errors.\nfor source in ["[1, 2 3]", "x = 1 +", "print \'x\'", "import a.b from c.d", "case 1: pass", "match x\\n  case 1: pass",\n               "x = 08", "0x", "0o8", "1_000_", "1.5j_", "with a,: pass", "raise from x", "3 + not 3", "- not 3", "{1: 2, 3}",\n               "{1:}", "f(x for x in y, 1)", "f(a, x for x in y if z)", "\'a\' b \'c\'", "x = pass if 1 else 1", "[a b",\n               "[a b c", "from t import x,", "import a as b.c", "try:\\n  pass\\nexcept E as a.b:\\n  pass", "x = \'abc",\n               "x = f\'abc", "match x:\\n  case 1 as a():\\n    pass", "fur x in y:\\n  pass", "class C(x for x in y): pass",\n               "for x im y:\\n  pass"]:\n    try:\n        compile(source, "<s>", "exec")\n    except SyntaxError as e:\n        print(type(e).__name__, e.msg, e.lineno, e.offset, e.end_lineno, e.end_offset)\nnamespace = {}\nexec(compile(\'def g():\\n    return f"{(yield 1)}"\\n\', "<s>", "exec"), namespace)\nprint(next(namespace["g"]()))\nfor source in [\'x = f"{yield}"\', \'x = f"{await y}"\', \'x = (await\\n  y)\']:\n    try: compile(source, "<s>", "exec")\n    except SyntaxError as e: print(e.msg, e.lineno)\n',
              '''SyntaxError invalid syntax. Perhaps you forgot a comma? 1 5 1 8
SyntaxError invalid syntax 1 8 1 9
SyntaxError Missing parentheses in call to 'print'. Did you mean print(...)? 1 1 1 10
SyntaxError Did you mean to use 'from ... import ...' instead? 1 1 1 20
SyntaxError case statement must be inside match statement 1 1 1 8
SyntaxError expected ':' 1 8 1 9
SyntaxError leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers 1 5 1 6
SyntaxError invalid hexadecimal literal 1 2 1 2
SyntaxError invalid digit '8' in octal literal 1 3 1 3
SyntaxError invalid decimal literal 1 6 1 6
SyntaxError invalid imaginary literal 1 4 1 4
SyntaxError the last 'with' item has a trailing comma 1 7 1 8
SyntaxError did you forget an expression between 'raise' and 'from'? 1 1 1 11
SyntaxError 'not' after an operator must be parenthesized 1 5 1 10
SyntaxError 'not' after an operator must be parenthesized 1 3 1 8
SyntaxError ':' expected after dictionary key 1 8 1 0
SyntaxError expression expected after dictionary key and ':' 1 3 1 4
SyntaxError Generator expression must be parenthesized 1 3 1 15
SyntaxError Generator expression must be parenthesized 1 6 1 23
SyntaxError invalid syntax. Is this intended to be part of the string? 1 5 1 6
SyntaxError expected expression before 'if', but statement is given 1 5 1 9
SyntaxError '[' was never closed 1 1 1 0
SyntaxError invalid syntax. Perhaps you forgot a comma? 1 2 1 5
SyntaxError trailing comma not allowed without surrounding parentheses 1 17 1 18
SyntaxError cannot use attribute as import target 1 13 1 16
SyntaxError cannot use except statement with attribute 3 13 3 16
SyntaxError unterminated string literal (detected at line 1) 1 5 1 5
SyntaxError unterminated f-string literal (detected at line 1) 1 5 1 5
SyntaxError cannot use function call as pattern target 2 13 2 16
SyntaxError invalid syntax 1 5 1 6
SyntaxError invalid syntax 1 11 1 14
SyntaxError invalid syntax 1 7 1 9
1
'yield' outside function 1
'await' outside function 1
'await' outside function 1
''')

check_program('extra = [\'x = a < b = 1\',\'x = f() = y = 1\',\'x = 1 = 2\',\'[1] + 2 = 3\',\'(a) + 1 = 2\',\'[x for x in y] = 1\',\'x() = yield\',\'x = f() = 1 if 2 else 3\',\'-1 = 2\',\'not a = 1\',\'a, f() = 1\',\'*a = 1\',\'*a += 1\',\'del *a\',\'del (a, f())\',\'if x == 1 = 2: pass\',\'x = (yield) = 1\',\'f() = 1 = 2\',\'a.b, c() = 1\',\'x = lambda: 1 = 2\',\'await x = 1\',\'(x = 1)\',\'[a, b() = 1]\',\'x = f() == 1 = 2\',\'x = 1\',\'a, b = 1, 2\',\'x = y = z = 0\',\'a[0], b.c = 1, 2\',\'*a, b = c\',\'[a, *b] = c\',\'(a) = 1\',\'x += 1\',\'del a, b[0], c.d\',\'for (a, b) in c: pass\',\'with a as (b, c): pass\',\'[x for (a, b) in y]\',\'assert x == 1, "m"\',\'assert (x := 1)\',\'assert x := 1\',\'assert 1, x := 2\',\'f(a) = 1 = 2\',\'a, *b() = 1\',\'(a, b()) = 1\',\'x = [y = 1]\']\nfor src in [\'None = 1\', \'True = 1\', \'(True := 1)\', \'f() = 1\', \'yield = 1\', \'del f()\', \'a + 1 = 2\', \'1 = 1\', \'"abc" = 1\', \'b"" = 1\', \'... = 1\', \'(a, "b", c) = (1, 2, 3)\', \'(a, True, c) = (1, 2, 3)\', \'(a, *True, c) = (1, 2, 3)\', \'[a, b, c + 1] = [1, 2, 3]\', \'[a, b[1], c + 1] = [1, 2, 3]\', \'[a, b.c.d, c + 1] = [1, 2, 3]\', \'a if 1 else b = 1\', \'True = True = 3\', \'x = y = True = z = 3\', \'x = y = yield = 1\', \'a, b += 1, 2\', \'(a, b) += 1, 2\', \'[a, b] += 1, 2\', \'for a() in b: pass\', \'for (a, b()) in b: pass\', \'for [a, b()] in b: pass\', \'for (*a, b, c+1) in b: pass\', \'for (x, *(y, z.d())) in b: pass\', \'for a, b() in c: pass\', \'for a, b, (c + 1, d()): pass\', \'with a as b(): pass\', \'with a as (b, c()): pass\', \'with a as [b, c()]: pass\', \'with a as (*b, c, d+1): pass\', \'with a as (x, *(y, z.d())): pass\', \'with a as b, c as d(): pass\', \'[x for x() in a]\', \'[x for a, b, (c + 1, d()) in y]\', \'[x for x+1 in y]\', \'[x for x+1, x() in y]\', \'f(True=1)\', \'f(False=1)\', \'f(None=1)\', \'f(*args=[0])\', \'f(a, b, *args=[0])\', "f(**kwargs={\'a\': 1})", "f(a, b, *args, **kwargs={\'a\': 1})", \'None += 1\', \'f() += 1\', \'if 1:\\n  x() = 1\\nelif 1:\\n  pass\', \'if 1:\\n  pass\\nelif 1:\\n  x() = 1\', \'if 1:\\n  x() = 1\\nelif 1:\\n  pass\\nelse:\\n  pass\', \'if 1:\\n  pass\\nelif 1:\\n  x() = 1\\nelse:\\n  pass\', \'if 1:\\n  pass\\nelif 1:\\n  pass\\nelse:\\n  x() = 1\', \'if x = 3:\\n   pass\', \'while x = 3:\\n   pass\', \'if x.a = 3:\\n   pass\', \'while x.a = 3:\\n   pass\', \'{1, 2, 3} = 42\', \'{1: 2, 3: 4} = 42\', "f\'{x}\' = 42", "f\'{x}-{y}\' = 42", "t\'{x}\' = 42", "t\'{x}-{y}\' = 42", \'(x, y, z=3, d, e)\', \'[x, y, z=3, d, e]\', \'[z=3]\', \'{x, y, z=3, d, e}\', \'{z=3}\', \'import a as b; None = 1\', \'import a, b as c; d = 1; None = 1\', \'from a import b as c; None = 1\', \'from a import b, c as d; e = 1; None = 1\', \'assert a := 1\', \'assert 1, a := 1\', \'assert 1 = 2 = 3\', \'assert 1 = 2\', \'assert (1 = 2)\', "assert \'a\' = a", \'assert x[0] = 1\', \'assert (yield a) = 2\', \'assert a = 2\', \'assert (a = 2)\', \'assert a = b\', \'assert 1, 1 = b\', \'assert 1, (1 = b)\', \'assert 1, a = 1\', \'assert 1, (a = 1)\', \'assert 1 = a, a = 1\'] + extra:\n    try: compile(src, \'<s>\', \'exec\'); print(repr(src), \'OK\')\n    except SyntaxError as e: print(repr(src), e.msg, e.lineno)\nfor src in [\'A[*(1:2)]\', \'A[*]\', \'f(**x, *)\', \'f(x = 5, *:)\', \'f(**x, *y)\', \'f(a=)\', \'f((x)=2)\', \'f(True=1)\', "f(**kwargs={\'a\': 1})"]:\n    try: compile(src, \'<s>\', \'exec\')\n    except SyntaxError as e: print(repr(src), e.msg)\n',
              '\'None = 1\' cannot assign to None 1\n\'True = 1\' cannot assign to True 1\n\'(True := 1)\' cannot use assignment expressions with True 1\n\'f() = 1\' cannot assign to function call here. Maybe you meant \'==\' instead of \'=\'? 1\n\'yield = 1\' assignment to yield expression not possible 1\n\'del f()\' cannot delete function call 1\n\'a + 1 = 2\' cannot assign to expression here. Maybe you meant \'==\' instead of \'=\'? 1\n\'1 = 1\' cannot assign to literal here. Maybe you meant \'==\' instead of \'=\'? 1\n\'"abc" = 1\' cannot assign to literal here. Maybe you meant \'==\' instead of \'=\'? 1\n\'b"" = 1\' cannot assign to literal here. Maybe you meant \'==\' instead of \'=\'? 1\n\'... = 1\' cannot assign to ellipsis here. Maybe you meant \'==\' instead of \'=\'? 1\n\'(a, "b", c) = (1, 2, 3)\' cannot assign to literal 1\n\'(a, True, c) = (1, 2, 3)\' cannot assign to True 1\n\'(a, *True, c) = (1, 2, 3)\' cannot assign to True 1\n\'[a, b, c + 1] = [1, 2, 3]\' cannot assign to expression 1\n\'[a, b[1], c + 1] = [1, 2, 3]\' cannot assign to expression 1\n\'[a, b.c.d, c + 1] = [1, 2, 3]\' cannot assign to expression 1\n\'a if 1 else b = 1\' cannot assign to conditional expression 1\n\'True = True = 3\' cannot assign to True 1\n\'x = y = True = z = 3\' cannot assign to True 1\n\'x = y = yield = 1\' assignment to yield expression not possible 1\n\'a, b += 1, 2\' \'tuple\' is an illegal expression for augmented assignment 1\n\'(a, b) += 1, 2\' \'tuple\' is an illegal expression for augmented assignment 1\n\'[a, b] += 1, 2\' \'list\' is an illegal expression for augmented assignment 1\n\'for a() in b: pass\' cannot assign to function call 1\n\'for (a, b()) in b: pass\' cannot assign to function call 1\n\'for [a, b()] in b: pass\' cannot assign to function call 1\n\'for (*a, b, c+1) in b: pass\' cannot assign to expression 1\n\'for (x, *(y, z.d())) in b: pass\' cannot assign to function call 1\n\'for a, b() in c: pass\' cannot assign to function call 1\n\'for a, b, (c + 1, d()): pass\' cannot assign to expression 1\n\'with a as b(): pass\' cannot assign to function call 1\n\'with a as (b, c()): pass\' cannot assign to function call 1\n\'with a as [b, c()]: pass\' cannot assign to function call 1\n\'with a as (*b, c, d+1): pass\' cannot assign to expression 1\n\'with a as (x, *(y, z.d())): pass\' cannot assign to function call 1\n\'with a as b, c as d(): pass\' cannot assign to function call 1\n\'[x for x() in a]\' cannot assign to function call 1\n\'[x for a, b, (c + 1, d()) in y]\' cannot assign to expression 1\n\'[x for x+1 in y]\' cannot assign to expression 1\n\'[x for x+1, x() in y]\' cannot assign to expression 1\n\'f(True=1)\' cannot assign to True 1\n\'f(False=1)\' cannot assign to False 1\n\'f(None=1)\' cannot assign to None 1\n\'f(*args=[0])\' cannot assign to iterable argument unpacking 1\n\'f(a, b, *args=[0])\' cannot assign to iterable argument unpacking 1\n"f(**kwargs={\'a\': 1})" cannot assign to keyword argument unpacking 1\n"f(a, b, *args, **kwargs={\'a\': 1})" cannot assign to keyword argument unpacking 1\n\'None += 1\' \'None\' is an illegal expression for augmented assignment 1\n\'f() += 1\' \'function call\' is an illegal expression for augmented assignment 1\n\'if 1:\\n  x() = 1\\nelif 1:\\n  pass\' cannot assign to function call here. Maybe you meant \'==\' instead of \'=\'? 2\n\'if 1:\\n  pass\\nelif 1:\\n  x() = 1\' cannot assign to function call here. Maybe you meant \'==\' instead of \'=\'? 4\n\'if 1:\\n  x() = 1\\nelif 1:\\n  pass\\nelse:\\n  pass\' cannot assign to function call here. Maybe you meant \'==\' instead of \'=\'? 2\n\'if 1:\\n  pass\\nelif 1:\\n  x() = 1\\nelse:\\n  pass\' cannot assign to function call here. Maybe you meant \'==\' instead of \'=\'? 4\n\'if 1:\\n  pass\\nelif 1:\\n  pass\\nelse:\\n  x() = 1\' cannot assign to function call here. Maybe you meant \'==\' instead of \'=\'? 6\n\'if x = 3:\\n   pass\' invalid syntax. Maybe you meant \'==\' or \':=\' instead of \'=\'? 1\n\'while x = 3:\\n   pass\' invalid syntax. Maybe you meant \'==\' or \':=\' instead of \'=\'? 1\n\'if x.a = 3:\\n   pass\' cannot assign to attribute here. Maybe you meant \'==\' instead of \'=\'? 1\n\'while x.a = 3:\\n   pass\' cannot assign to attribute here. Maybe you meant \'==\' instead of \'=\'? 1\n\'{1, 2, 3} = 42\' cannot assign to set display here. Maybe you meant \'==\' instead of \'=\'? 1\n\'{1: 2, 3: 4} = 42\' cannot assign to dict literal here. Maybe you meant \'==\' instead of \'=\'? 1\n"f\'{x}\' = 42" cannot assign to f-string expression here. Maybe you meant \'==\' instead of \'=\'? 1\n"f\'{x}-{y}\' = 42" cannot assign to f-string expression here. Maybe you meant \'==\' instead of \'=\'? 1\n"t\'{x}\' = 42" cannot assign to t-string expression here. Maybe you meant \'==\' instead of \'=\'? 1\n"t\'{x}-{y}\' = 42" cannot assign to t-string expression here. Maybe you meant \'==\' instead of \'=\'? 1\n\'(x, y, z=3, d, e)\' invalid syntax. Maybe you meant \'==\' or \':=\' instead of \'=\'? 1\n\'[x, y, z=3, d, e]\' invalid syntax. Maybe you meant \'==\' or \':=\' instead of \'=\'? 1\n\'[z=3]\' invalid syntax. Maybe you meant \'==\' or \':=\' instead of \'=\'? 1\n\'{x, y, z=3, d, e}\' invalid syntax. Maybe you meant \'==\' or \':=\' instead of \'=\'? 1\n\'{z=3}\' invalid syntax. Maybe you meant \'==\' or \':=\' instead of \'=\'? 1\n\'import a as b; None = 1\' cannot assign to None 1\n\'import a, b as c; d = 1; None = 1\' cannot assign to None 1\n\'from a import b as c; None = 1\' cannot assign to None 1\n\'from a import b, c as d; e = 1; None = 1\' cannot assign to None 1\n\'assert a := 1\' cannot use named expression without parentheses here 1\n\'assert 1, a := 1\' cannot use named expression without parentheses here 1\n\'assert 1 = 2 = 3\' cannot assign to literal here. Maybe you meant \'==\' instead of \'=\'? 1\n\'assert 1 = 2\' cannot assign to literal here. Maybe you meant \'==\' instead of \'=\'? 1\n\'assert (1 = 2)\' cannot assign to literal here. Maybe you meant \'==\' instead of \'=\'? 1\n"assert \'a\' = a" cannot assign to literal here. Maybe you meant \'==\' instead of \'=\'? 1\n\'assert x[0] = 1\' cannot assign to subscript here. Maybe you meant \'==\' instead of \'=\'? 1\n\'assert (yield a) = 2\' cannot assign to yield expression here. Maybe you meant \'==\' instead of \'=\'? 1\n\'assert a = 2\' cannot assign to name here. Maybe you meant \'==\' instead of \'=\'? 1\n\'assert (a = 2)\' invalid syntax. Maybe you meant \'==\' or \':=\' instead of \'=\'? 1\n\'assert a = b\' cannot assign to name here. Maybe you meant \'==\' instead of \'=\'? 1\n\'assert 1, 1 = b\' cannot assign to literal here. Maybe you meant \'==\' instead of \'=\'? 1\n\'assert 1, (1 = b)\' cannot assign to literal here. Maybe you meant \'==\' instead of \'=\'? 1\n\'assert 1, a = 1\' cannot assign to name here. Maybe you meant \'==\' instead of \'=\'? 1\n\'assert 1, (a = 1)\' invalid syntax. Maybe you meant \'==\' or \':=\' instead of \'=\'? 1\n\'assert 1 = a, a = 1\' cannot assign to literal here. Maybe you meant \'==\' instead of \'=\'? 1\n\'x = a < b = 1\' invalid syntax. Maybe you meant \'==\' or \':=\' instead of \'=\'? 1\n\'x = f() = y = 1\' cannot assign to function call 1\n\'x = 1 = 2\' cannot assign to literal 1\n\'[1] + 2 = 3\' cannot assign to expression 1\n\'(a) + 1 = 2\' cannot assign to expression here. Maybe you meant \'==\' instead of \'=\'? 1\n\'[x for x in y] = 1\' cannot assign to list comprehension here. Maybe you meant \'==\' instead of \'=\'? 1\n\'x() = yield\' cannot assign to function call 1\n\'x = f() = 1 if 2 else 3\' cannot assign to function call 1\n\'-1 = 2\' cannot assign to expression here. Maybe you meant \'==\' instead of \'=\'? 1\n\'not a = 1\' cannot assign to expression 1\n\'a, f() = 1\' cannot assign to function call here. Maybe you meant \'==\' instead of \'=\'? 1\n\'*a = 1\' starred assignment target must be in a list or tuple 1\n\'*a += 1\' \'starred\' is an illegal expression for augmented assignment 1\n\'del *a\' cannot delete starred 1\n\'del (a, f())\' cannot delete function call 1\n\'if x == 1 = 2: pass\' invalid syntax 1\n\'x = (yield) = 1\' cannot assign to yield expression 1\n\'f() = 1 = 2\' cannot assign to function call 1\n\'a.b, c() = 1\' cannot assign to function call here. Maybe you meant \'==\' instead of \'=\'? 1\n\'x = lambda: 1 = 2\' cannot assign to lambda 1\n\'await x = 1\' cannot assign to await expression here. Maybe you meant \'==\' instead of \'=\'? 1\n\'(x = 1)\' invalid syntax. Maybe you meant \'==\' or \':=\' instead of \'=\'? 1\n\'[a, b() = 1]\' cannot assign to function call here. Maybe you meant \'==\' instead of \'=\'? 1\n\'x = f() == 1 = 2\' invalid syntax. Maybe you meant \'==\' or \':=\' instead of \'=\'? 1\n\'x = 1\' OK\n\'a, b = 1, 2\' OK\n\'x = y = z = 0\' OK\n\'a[0], b.c = 1, 2\' OK\n\'*a, b = c\' OK\n\'[a, *b] = c\' OK\n\'(a) = 1\' OK\n\'x += 1\' OK\n\'del a, b[0], c.d\' OK\n\'for (a, b) in c: pass\' OK\n\'with a as (b, c): pass\' OK\n\'[x for (a, b) in y]\' OK\n\'assert x == 1, "m"\' OK\n\'assert (x := 1)\' OK\n\'assert x := 1\' cannot use named expression without parentheses here 1\n\'assert 1, x := 2\' cannot use named expression without parentheses here 1\n\'f(a) = 1 = 2\' cannot assign to function call 1\n\'a, *b() = 1\' cannot assign to function call 1\n\'(a, b()) = 1\' cannot assign to function call 1\n\'x = [y = 1]\' invalid syntax. Maybe you meant \'==\' or \':=\' instead of \'=\'? 1\n\'A[*(1:2)]\' Invalid star expression\n\'A[*]\' Invalid star expression\n\'f(**x, *)\' Invalid star expression\n\'f(x = 5, *:)\' Invalid star expression\n\'f(**x, *y)\' iterable argument unpacking follows keyword argument unpacking\n\'f(a=)\' expected argument value expression\n\'f((x)=2)\' expression cannot contain assignment, perhaps you meant "=="?\n\'f(True=1)\' cannot assign to True\n"f(**kwargs={\'a\': 1})" cannot assign to keyword argument unpacking\n')

check_program('''[await x for x in a]
''',
              '''SyntaxError: asynchronous comprehension outside of an asynchronous function (<program>, line 1)
''')

check_program('''async def f():
    return [await x for x in a]
f().send(None)
''',
              '''NameError: name 'a' is not defined
''')

check_program('''await x
''',
              '''SyntaxError: 'await' outside function (<program>, line 1)
''')

check_program('''async def f():
    def g():
        return await x
''',
              '''SyntaxError: 'await' outside async function (<program>, line 3)
''')
