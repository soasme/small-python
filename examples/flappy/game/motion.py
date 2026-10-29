"""Smooth motion without a math module: the engine core has none."""
PI = 3.141592653589793


def sine(x):
    """Bhaskara I's approximation of sin(x), within 0.002 of it."""
    x %= 2 * PI
    sign = 1
    if x > PI:
        x, sign = x - PI, -1
    p = x * (PI - x)
    return sign * 16 * p / (5 * PI * PI - 4 * p)


def approach(value, target, rate, dt):
    """Move value toward target, closing the gap at rate per second."""
    return value + (target - value) * min(1.0, rate * dt)
