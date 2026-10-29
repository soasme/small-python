# build:
# bundles: packages.py shop/__init__.py shop/cart.py shop/pricing/__init__.py shop/pricing/table.py shop/pricing/rules.py
# description: relative imports (PEP 328) from packages, subpackages, and modules, with from . import and from .. import.
import shop
from shop.pricing import rules
assert shop.total(["apple", "pear"]) == 8
assert rules.cart is shop.cart and rules.total is shop.cart.total
assert shop.pricing.__package__ == "shop.pricing" and rules.__package__ == "shop.pricing"
assert shop.cart.pricing is shop.pricing
