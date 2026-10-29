# build: -x ext
# bundles: externals.py
# description: an external module and its submodules are left to the host, and their own imports are not followed.
try:
    import ext
except ImportError as error:
    failure = error
try:
    import ext.sub
except ImportError as error:
    sub_failure = error
assert isinstance(failure, ImportError) and isinstance(sub_failure, ImportError)
