def accumulate():
    total = 0
    try:
        while True:
            value = yield total
            if value is None:
                return total
            total += value
    finally:
        print("accumulator closed")


def session():
    total = yield from accumulate()
    print("total:", total)


values = session()
print(next(values))
print(values.send(10))
print(values.send(20))
print(next(values, "done"))
