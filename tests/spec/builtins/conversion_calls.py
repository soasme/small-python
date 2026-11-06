# spec: PLS-315 7.5.5, 7.5.6, 19.3.32, 23.1.1
# description: str() and repr() of an instance call its class's __str__ or
# __repr__, str() falling back to __repr__; the result must be a str, and
# a str subclass it returns is the value. What they raise reaches the
# caller. Each holds at module level and inside a function.
from harness import *

class Both:
    def __str__(self):
        for i in range(2): pass
        return 'both!'
    def __repr__(self): return 'Both()'

class OnlyRepr:
    def __repr__(self):
        for i in range(2): pass
        return 'OnlyRepr()'

class Bad:
    def __str__(self): return 5

class Text(str):
    pass

class Subclassed:
    def __str__(self): return Text('sub')

class Failing:
    def __repr__(self): raise KeyError('r')

def converted():
    out = [str(Both()), repr(Both()), str(OnlyRepr()), repr(OnlyRepr())]
    try:
        str(Bad())
    except TypeError as e:
        out.append(str(e))
    x = str(Subclassed())
    out.append((x, type(x) is Text))
    try:
        repr(Failing())
    except KeyError as e:
        out.append(e.args)
    args = [Both()]
    out.append(str(*args))
    return out

assert converted() == ['both!', 'Both()', 'OnlyRepr()', 'OnlyRepr()', 'Bad.__str__() must return a str, not int',
                       ('sub', True), ('r',), 'both!'], converted()

assert str(Both()) == 'both!' and repr(OnlyRepr()) == 'OnlyRepr()'
assert type(str(Subclassed())) is Text

# The method the class holds when str() is called is the one that runs.
class Changing:
    def __str__(self):
        del Changing.__str__
        return 'first'
    def __repr__(self): return 'then repr'

c = Changing()
assert (str(c), str(c)) == ('first', 'then repr')
