"""This module provides access to the garbage collector for reference cycles.

Small Python builds this module into the engine, following CPython 3.15's gc
module. Reference counting frees most values at once; collect() runs the
engine's cycle collector, which has a single generation. Automatic
collection happens between host runs, so enable(), disable() and the
thresholds are recorded but do not schedule collections. Objects are never
uncollectable, so garbage stays empty.
"""

DEBUG_STATS = 1
DEBUG_COLLECTABLE = 2
DEBUG_UNCOLLECTABLE = 4
DEBUG_SAVEALL = 32
DEBUG_LEAK = DEBUG_COLLECTABLE | DEBUG_UNCOLLECTABLE | DEBUG_SAVEALL

garbage = []
callbacks = []
_state = {'enabled': True, 'debug': 0, 'threshold': (2000, 10, 10), 'collections': 0, 'collected': 0}


def _generation(value):
    value = range(value).stop
    if not 0 <= value <= 2:
        raise ValueError('invalid generation')
    return value


def enable():
    """Enable automatic garbage collection."""
    _state['enabled'] = True


def disable():
    """Disable automatic garbage collection."""
    _state['enabled'] = False


def isenabled():
    """Returns true if automatic garbage collection is enabled."""
    return _state['enabled']


def collect(generation=2):
    """Run the garbage collector.

With no arguments, run a full collection.  The optional argument
may be an integer specifying which generation to collect.  A ValueError
is raised if the generation number is invalid.

The number of unreachable objects is returned."""
    generation = _generation(generation)
    for callback in list(callbacks):
        callback('start', {'generation': generation, 'collected': 0, 'uncollectable': 0})
    count = _collect()
    _state['collections'] += 1
    _state['collected'] += count
    for callback in list(callbacks):
        callback('stop', {'generation': generation, 'collected': count, 'uncollectable': 0})
    return count


def get_count():
    """Return a three-tuple of the current collection counts."""
    return (0, 0, 0)


def get_threshold():
    """Return the current collection thresholds."""
    return _state['threshold']


def set_threshold(*args):
    """set_threshold(threshold0, [threshold1, [threshold2]])
Set the collection thresholds (the collection frequency).

Setting 'threshold0' to zero disables collection."""
    if not 1 <= len(args) <= 3:
        raise TypeError('gc.set_threshold requires 1 to 3 arguments')
    values = [range(arg).stop for arg in args]
    current = list(_state['threshold'])
    current[:len(values)] = values
    _state['threshold'] = tuple(current)


def get_debug():
    """Get the garbage collection debugging flags."""
    return _state['debug']


def set_debug(flags, /):
    """Set the garbage collection debugging flags.

  flags
    An integer that can have the following bits turned on:
      DEBUG_STATS - Print statistics during collection.
      DEBUG_COLLECTABLE - Print collectable objects found.
      DEBUG_UNCOLLECTABLE - Print unreachable but uncollectable objects
        found.
      DEBUG_SAVEALL - Save objects to gc.garbage rather than freeing them.
      DEBUG_LEAK - Debug leaking programs (everything but STATS).

Debugging information is written to sys.stderr."""
    _state['debug'] = range(flags).stop


def get_stats():
    """Return a list of dictionaries containing per-generation statistics."""
    stats = [{'collections': 0, 'collected': 0, 'uncollectable': 0} for _ in range(3)]
    stats[2]['collections'] = _state['collections']
    stats[2]['collected'] = _state['collected']
    return stats


def get_objects(generation=None):
    """Return a list of objects tracked by the collector (excluding the list returned).

  generation
    Generation to extract the objects from.

If generation is not None, return only the objects tracked by the collector
that are in that generation."""
    if generation is not None:
        generation = range(generation).stop
        if generation >= 3:
            raise ValueError(f'generation parameter must be less than the number of available generations (3)')
        if generation < 0:
            raise ValueError('generation parameter cannot be negative')
    return _objects()


def is_tracked(obj, /):
    """Returns true if the object is tracked by the garbage collector.

Simple atomic objects will return false."""
    return _tracked(obj)


def is_finalized(obj, /):
    """Returns true if the object has been already finalized by the GC."""
    return False


def freeze():
    """Freeze all current tracked objects and ignore them for future collections.

This can be used before a POSIX fork() call to make the gc copy-on-write friendly.
Note: collection before a POSIX fork() call may free pages for future allocation
which can cause copy-on-write."""


def unfreeze():
    """Unfreeze all objects in the permanent generation.

Put all objects in the permanent generation back into oldest generation."""


def get_freeze_count():
    """Return the number of objects in the permanent generation."""
    return 0
