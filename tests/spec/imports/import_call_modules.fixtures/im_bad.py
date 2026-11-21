from log_mod import log
log.append('bad')
raise KeyError('bad body')
