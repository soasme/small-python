# build:
# bundles: cycles.py cycle_a.py cycle_b.py
# description: modules importing each other see the partially initialized module, and each runs once.
import cycle_a
import cycle_b
assert cycle_b.SEEN == "partial" and cycle_a.STATE == "done"
assert cycle_b.cycle_a is cycle_a and cycle_a.cycle_b is cycle_b
