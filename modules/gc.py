"""This module provides access to the garbage collector for reference cycles.

Small Python's standard layer (spy-std.c) provides this module as
docs/standards/std.md specifies it, after CPython 3.15's gc module. Reference counting
frees most values at once; collect() runs the engine's cycle collector,
which has a single generation; freeze() makes the values it tracks roots
of every collection. Automatic collection happens between host runs, so
enable(), disable() and the thresholds are recorded but do not schedule
collections. Debugging reports go to sys.stderr.
"""

from _spy import (get_referents, get_referrers, get_count, freeze, unfreeze, get_freeze_count, _collect, _tracked,
                  _finalized, _objects)

DEBUG_STATS = 1
DEBUG_COLLECTABLE = 2
DEBUG_UNCOLLECTABLE = 4
DEBUG_SAVEALL = 32
DEBUG_LEAK = DEBUG_COLLECTABLE | DEBUG_UNCOLLECTABLE | DEBUG_SAVEALL

garbage = []
callbacks = []


def _define(collect_now, tracked, finalized, objects):
    # The collector's settings, shared by the functions below and private to them.
    enabled = [True]
    debug = [0]
    threshold = [(2000, 10, 10)]
    stats = [{'collections': 0, 'collected': 0, 'uncollectable': 0, 'candidates': 0, 'duration': 0.0}
             for _ in range(3)]

    def c_function(arity):
        # CPython's checks for a C function taking no argument or exactly one.
        def wrap(function):
            name = f"gc.{function.__name__}"

            def call(*args, **kwargs):
                if kwargs:
                    raise TypeError(f"{name}() takes no keyword arguments")
                if len(args) != arity:
                    raise TypeError(f"{name}() takes no arguments ({len(args)} given)" if not arity else
                                    f"{name}() takes exactly one argument ({len(args)} given)")
                return function(*args)
            call.__name__, call.__doc__ = function.__name__, function.__doc__
            return call
        return wrap

    def report(text):
        # Debugging output, as CPython's PySys_WriteStderr.
        import sys
        sys.stderr.write(text)

    def at_most_one(name, keyword, args, kwargs):
        # An optional argument given by position or keyword, as CPython's clinic parses it.
        if len(args) + len(kwargs) > 1:
            raise TypeError(f"{name}() takes at most 1 argument ({len(args) + len(kwargs)} given)")
        for key in kwargs:
            if key != keyword:
                raise TypeError(f"{name}() got an unexpected keyword argument '{key}'")
        return args or tuple(kwargs.values())

    @c_function(0)
    def enable():
        """Enable automatic garbage collection."""
        enabled[0] = True

    @c_function(0)
    def disable():
        """Disable automatic garbage collection."""
        enabled[0] = False

    @c_function(0)
    def isenabled():
        """Returns true if automatic garbage collection is enabled."""
        return enabled[0]

    def collect(*args, **kwargs):
        """Run the garbage collector.

With no arguments, run a full collection.  The optional argument
may be an integer specifying which generation to collect.  A ValueError
is raised if the generation number is invalid.

The number of unreachable objects is returned."""
        generation = range(*at_most_one("collect", "generation", args, kwargs) or (2,)).stop
        if not 0 <= generation <= 2:
            raise ValueError('invalid generation')
        info = {'generation': generation, 'collected': 0, 'uncollectable': 0, 'candidates': 0, 'duration': 0.0}
        for callback in list(callbacks):
            callback('start', info)
        if debug[0] & DEBUG_STATS:
            report(f"gc: collecting generation {generation}...\n"
                   f"gc: objects in each generation: {get_count()[0]} 0 0\n"
                   f"gc: objects in permanent generation: {get_freeze_count()}\n")
        count, candidates, duration, collectable = collect_now(garbage if debug[0] & DEBUG_SAVEALL else None,
                                                               debug[0] & DEBUG_COLLECTABLE)
        if collectable:
            report(collectable)
        if debug[0] & DEBUG_STATS:
            report(f"gc: done, {count} unreachable, 0 uncollectable, {duration:.4f}s elapsed\n")
        counts = stats[generation]
        counts['collections'] += 1
        counts['collected'] += count
        counts['candidates'] += candidates
        counts['duration'] += duration
        info = dict(info, collected=count, candidates=candidates, duration=duration)
        for callback in list(callbacks):
            callback('stop', info)
        return count

    @c_function(0)
    def get_threshold():
        """Return the current collection thresholds."""
        return threshold[0]

    def set_threshold(*args, **kwargs):
        """set_threshold(threshold0, [threshold1, [threshold2]])
Set the collection thresholds (the collection frequency).

Setting 'threshold0' to zero disables collection."""
        if kwargs:
            raise TypeError("set_threshold() takes no keyword arguments")
        if not 1 <= len(args) <= 3:
            raise TypeError('gc.set_threshold requires 1 to 3 arguments')
        values = [range(arg).stop for arg in args]
        if any(not -2**63 <= value < 2**63 for value in values):
            raise OverflowError("Python int too large to convert to C long")
        threshold[0] = tuple(values) + threshold[0][len(values):]

    @c_function(0)
    def get_debug():
        """Get the garbage collection debugging flags."""
        return debug[0]

    @c_function(1)
    def set_debug(flags):
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
        debug[0] = range(flags).stop

    @c_function(0)
    def get_stats():
        """Return a list of dictionaries containing per-generation statistics."""
        return [dict(counts) for counts in stats]

    def get_objects(*args, **kwargs):
        """Return a list of objects tracked by the collector (excluding the list returned).

  generation
    Generation to extract the objects from.

If generation is not None, return only the objects tracked by the collector
that are in that generation."""
        generation = (at_most_one("get_objects", "generation", args, kwargs) or (None,))[0]
        if generation is not None:
            if not isinstance(generation, int) and not hasattr(type(generation), "__index__"):
                raise TypeError(f"argument should be integer or None, not '{type(generation).__name__}'")
            if range(generation).stop >= 3:
                raise ValueError('generation parameter must be less than the number of available generations (3)')
        return objects()

    @c_function(1)
    def is_tracked(obj):
        """Returns true if the object is tracked by the garbage collector.

Simple atomic objects will return false."""
        return tracked(obj)

    @c_function(1)
    def is_finalized(obj):
        """Returns true if the object has been already finalized by the GC."""
        return finalized(obj)

    public = {name: value for name, value in locals().items()
              if callable(value) and name not in ('c_function', 'at_most_one', 'report', 'collect_now', 'tracked',
                                                  'finalized', 'objects')}
    for function in public.values():
        function.__qualname__ = function.__name__
    return public


globals().update(_define(_collect, _tracked, _finalized, _objects))
del _define, _collect, _tracked, _finalized, _objects
