# build:
# bundles: encoding.py latin.py bom.py
# description: modules are embedded byte for byte and decoded at run time, honoring PEP 263 declarations and a UTF-8 BOM.
import latin
import bom
assert latin.TEXT == "caf\xe9" and bom.TEXT == "\u00e9t\u00e9"
