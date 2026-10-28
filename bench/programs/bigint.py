# Arbitrary-precision integer multiplication, division and formatting.
f = 1
for i in range(2, 1400):
    f *= i
s = str(f)
digits = 0
for c in s:
    digits += int(c)
print(len(s), digits, f % 1000000007, (f // (7 ** 500)) % 1000)
