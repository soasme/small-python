# Generator functions and delegation.
def count(n):
    i = 0
    while i < n:
        yield i
        i += 1

def evens(it):
    for x in it:
        if x % 2 == 0:
            yield x

def chain(n):
    yield from evens(count(n))
    yield from evens(count(n))

total = 0
for x in chain(500000):
    total += x * x
print(total)
