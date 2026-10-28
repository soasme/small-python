# Dictionary insertion, lookup and removal with integer and string keys.
d = {}
for i in range(200000):
    d[i] = i * 2
    d["k" + str(i % 5000)] = i
hits = 0
for i in range(0, 400000, 3):
    if i in d:
        hits += d[i]
for i in range(0, 200000, 2):
    d.pop(i)
print(len(d), hits)
