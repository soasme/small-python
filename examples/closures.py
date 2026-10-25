def multiplier(factor):
    def apply(value):
        return value * factor
    return apply

twice = multiplier(2)
print(twice(21))

cycle = []
cycle.append(cycle)
print(cycle)
