import tracelog
tracelog.events.append("cycle_b")
import cycle_a
B = getattr(cycle_a, "A", "partial")
