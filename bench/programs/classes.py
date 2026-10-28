# Object creation, attribute access and method calls.
class Vec:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def add(self, other):
        return Vec(self.x + other.x, self.y + other.y)

    def dot(self, other):
        return self.x * other.x + self.y * other.y

acc = Vec(0, 0)
step = Vec(1, 2)
total = 0
for i in range(300000):
    acc = acc.add(step)
    total += acc.dot(step) % 7
print(acc.x, acc.y, total)
