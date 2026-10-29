from .pricing import price
from . import pricing


def total(items):
    return sum(price(i) for i in items)
