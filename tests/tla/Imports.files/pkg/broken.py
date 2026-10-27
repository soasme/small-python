import tracelog
tracelog.events.append("broken")
raise ValueError("broken")
