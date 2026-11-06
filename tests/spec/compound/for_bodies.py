# spec: PLS-315 15.3, 15.2
# description: A for loop whose body is one statement or a run of simple
# statements runs the body once per item, in order, and break, continue,
# return and an exception leave it as they leave any loop body.
from harness import *

def single(n):
    total = 0
    for i in range(n):
        total = total + i
    return total, i

assert single(5) == (10, 4)

def block(items):
    seen = []
    for x in items:
        y = x * 2
        seen.append(y)
    return seen, x, y

assert block([1, 2, 3]) == ([2, 4, 6], 3, 6)
assert block((7,)) == ([14], 7, 14)

def leaving(n):
    out = []
    for i in range(n):
        if i == 1: continue
        if i == 3: break
        out.append(i)
    else:
        out.append('else')
    return out

assert leaving(5) == [0, 2]
assert leaving(1) == [0, 'else']

def returning(items):
    for x in items:
        if x > 2: return x
        x = 0
    return None

assert returning([1, 5, 2]) == 5
assert returning([]) is None

def raising(items):
    done = []
    for x in items:
        done.append(x)
        1 // x
    return done

try:
    raising([2, 1, 0, 3])
except ZeroDivisionError:
    pass
else:
    raise AssertionError('no ZeroDivisionError')

# Iterators other than ranges, lists and tuples, and a list that grows.
def keys(d):
    out = []
    for k in d:
        out.append(k)
    return out

assert keys({'a': 1, 'b': 2}) == ['a', 'b']
assert keys('xy') == ['x', 'y']

def growing():
    items = [1]
    for x in items:
        if x < 4: items.append(x + 1)
    return items

assert growing() == [1, 2, 3, 4]

def changed():
    d = {'a': 1}
    try:
        for k in d:
            d[k + k] = 0
    except RuntimeError as e:
        return str(e)

assert changed() == 'dictionary changed size during iteration'

# A long range in one statement's body, and a negative step.
def counting():
    n = 0
    for i in range(100000):
        n = n + 1
    for j in range(10, 0, -3):
        n = n - j
    return n, i, j

assert counting() == (100000 - 22, 99999, 1)

# A loop variable rebound in the body takes the next item regardless.
def rebinding():
    out = []
    for i in range(3):
        i = i * 10
        out.append(i)
    return out

assert rebinding() == [0, 10, 20]
