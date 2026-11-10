# bundles: std_modules.py
# description: an imported standard module is registered, not bundled, and a file of the same name does not shadow it.
import sys
assert sys.modules["sys"] is sys
