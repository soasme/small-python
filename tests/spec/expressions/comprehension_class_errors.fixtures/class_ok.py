class C:
    x = [1]
    y = [i * 2 for i in x]
    z = {k: v for k, v in [(1, 2)]}
    w = [a for a in x if a]
