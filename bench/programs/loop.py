# A tight interpreter loop over local integers.
total = 0
i = 0
while i < 3000000:
    if i % 3 == 0:
        total += i
    else:
        total -= 1
    i += 1
print(total)
