# Sorting integers, tuples and keyed records.
seed = 12345
data = []
for _ in range(100000):
    seed = (seed * 1103515245 + 12345) % 2147483648
    data.append(seed % 100000)
a = sorted(data)
b = sorted([(x % 100, x) for x in data], reverse=True)
c = sorted(data, key=lambda x: (x % 7, -x))
print(a[500], b[500], c[500])
