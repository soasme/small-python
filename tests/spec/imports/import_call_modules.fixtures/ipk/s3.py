from log_mod import log
log.append('s3')
rel = __import__('s1', globals(), None, ['x'], 1)
