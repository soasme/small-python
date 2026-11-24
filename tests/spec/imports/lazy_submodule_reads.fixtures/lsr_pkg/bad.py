from lsr_log import log
log.append("bad")
for _ in range(2): pass
raise ValueError("bad body")
