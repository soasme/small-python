# String building, splitting, formatting and counting.
words = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"]
counts = {}
total = 0
for i in range(60000):
    line = " ".join([words[(i + k) % 8] for k in range(5)])
    line = f"{i}:{line.upper()}"
    for w in line.split(":")[1].split(" "):
        counts[w] = counts.get(w, 0) + 1
    total += len(line.replace("A", "aa"))
print(total, sorted(counts.items())[0])
