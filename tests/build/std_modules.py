# build: -M sys
# bundles: std_modules.py
# description: a module registered with -M is not bundled, and a file of the same name does not shadow it.
import sys
assert sys.modules["sys"] is sys
