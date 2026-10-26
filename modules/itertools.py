"""Functional tools for creating and using iterators.

Small Python's standard layer (spy-std.c) provides this module, following CPython 3.15's
itertools C module: the same iterator types, argument checks, and error
messages, written in Python. Pickling support, which CPython 3.14 removed,
is not provided.
"""


def _index(value):
    # operator.index: range() accepts exactly the objects with __index__.
    return range(value).stop


def _is_number(value):
    # PyNumber_Check: the object has __index__, __int__, __float__ or is complex.
    cls = type(value)
    return (isinstance(value, (int, float, complex)) or hasattr(cls, '__index__')
            or hasattr(cls, '__int__') or hasattr(cls, '__float__'))


def _no_keywords(name, kwargs):
    if kwargs:
        raise TypeError(f'{name}() takes no keyword arguments')


def _arity(name, args, low, high=None):
    high = low if high is None else high
    if low == high and len(args) != low:
        raise TypeError(f"{name} expected {low} argument{'s' if low != 1 else ''}, got {len(args)}")
    if len(args) < low:
        raise TypeError(f'{name} expected at least {low} argument{"s" if low != 1 else ""}, got {len(args)}')
    if len(args) > high:
        raise TypeError(f'{name} expected at most {high} argument{"s" if high != 1 else ""}, got {len(args)}')


_maxsize = 9223372036854775807
_missing = object()


def _parse(name, args, kwargs, names, required, kwonly=()):
    # Argument Clinic's checks and messages for a constructor's parameters.
    total = len(args) + len(kwargs)
    if kwonly:
        if len(args) > len(names):
            quantity = 'exactly' if required == len(names) else 'at most'
            raise TypeError(f'{name}() takes {quantity} {len(names)} positional arguments ({len(args)} given)')
    elif total > len(names):
        raise TypeError(f'{name}() takes at most {len(names)} arguments ({total} given)')
    values = list(args) + [_missing] * (len(names) - len(args))
    extra = {}
    for key, value in kwargs.items():
        if key in names:
            index = names.index(key)
            if index < len(args):
                raise TypeError(f"argument for {name}() given by name ('{key}') and position ({index + 1})")
            values[index] = value
        elif key in kwonly:
            extra[key] = value
        else:
            raise TypeError(f"{name}() got an unexpected keyword argument '{key}'")
    for index in range(required):
        if values[index] is _missing:
            raise TypeError(f"{name}() missing required argument '{names[index]}' (pos {index + 1})")
    return values, extra


class count:
    """Return a count object whose .__next__() method returns consecutive values.

    Equivalent to:
        def count(firstval=0, step=1):
            x = firstval
            while 1:
                yield x
                x += step
    """

    def __new__(cls, *args, **kwargs):
        (start, step), _ = _parse('count', args, kwargs, ('start', 'step'), 0)
        start = 0 if start is _missing else start
        step = 1 if step is _missing else step
        if not _is_number(start) or not _is_number(step):
            raise TypeError('a number is required')
        self = object.__new__(cls)
        self._count = start
        self._step = step
        return self

    def __iter__(self):
        return self

    def __next__(self):
        value = self._count
        self._count = value + self._step
        return value

    def __repr__(self):
        name = type(self).__name__
        if isinstance(self._step, int) and self._step == 1:
            return f'{name}({self._count!r})'
        return f'{name}({self._count!r}, {self._step!r})'


class cycle:
    """Return elements from the iterable until it is exhausted. Then repeat the sequence indefinitely."""

    def __new__(cls, *args, **kwargs):
        if cls is cycle:
            _no_keywords('cycle', kwargs)
        _arity('cycle', args, 1)
        self = object.__new__(cls)
        self._it = iter(args[0])
        self._saved = []
        self._index = 0
        self._firstpass = True
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if self._it is not None:
            try:
                value = next(self._it)
            except StopIteration:
                self._it = None
            else:
                if self._firstpass:
                    self._saved.append(value)
                return value
        if not self._saved:
            raise StopIteration
        value = self._saved[self._index]
        self._index = (self._index + 1) % len(self._saved)
        return value


class repeat:
    """repeat(object [,times]) -> create an iterator which returns the object
for the specified number of times.  If not specified, returns the object
endlessly."""

    def __new__(cls, *args, **kwargs):
        names = ('object', 'times')
        if len(args) > 2:
            raise TypeError(f'repeat() takes at most 2 arguments ({len(args) + len(kwargs)} given)')
        values = dict(zip(names, args))
        for key, value in kwargs.items():
            if key not in names:
                raise TypeError(f"repeat() got an unexpected keyword argument '{key}'")
            if key in values:
                raise TypeError(f"argument for repeat() given by name ('{key}') and position ({names.index(key) + 1})")
            values[key] = value
        if 'object' not in values:
            raise TypeError("repeat() missing required argument 'object' (pos 1)")
        self = object.__new__(cls)
        self._element = values['object']
        times = values.get('times')
        self._count = None if 'times' not in values else max(_index(times), 0)
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if self._count is None:
            return self._element
        if self._count <= 0:
            raise StopIteration
        self._count -= 1
        return self._element

    def __length_hint__(self):
        if self._count is None:
            raise TypeError('len() of unsized object')
        return self._count

    def __repr__(self):
        name = type(self).__name__
        if self._count is None:
            return f'{name}({self._element!r})'
        return f'{name}({self._element!r}, {self._count})'


class accumulate:
    """Return series of accumulated sums (or other binary function results)."""

    def __new__(cls, *args, **kwargs):
        (iterable, func), extra = _parse('accumulate', args, kwargs, ('iterable', 'func'), 1, ('initial',))
        func = None if func is _missing else func
        initial = extra.get('initial')
        self = object.__new__(cls)
        self._it = iter(iterable)
        self._func = func
        self._total = None
        self._started = False
        self._initial = initial
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if self._initial is not None:
            self._total = self._initial
            self._initial = None
            self._started = True
            return self._total
        value = next(self._it)
        if not self._started:
            self._started = True
            self._total = value
        elif self._func is None:
            self._total = self._total + value
        else:
            self._total = self._func(self._total, value)
        return self._total


class batched:
    """Batch data into tuples of length n. The last batch may be shorter than n.

Loops over the input iterable and accumulates data into tuples
up to size n.  The input is consumed lazily, just enough to
fill a batch.  The result is yielded as soon as a batch is full
or when the input iterable is exhausted.

If "strict" is True, raises a ValueError if the final batch is shorter
than n."""

    def __new__(cls, *args, **kwargs):
        (iterable, n), extra = _parse('batched', args, kwargs, ('iterable', 'n'), 2, ('strict',))
        strict = extra.get('strict', False)
        n = _index(n)
        if n < 1:
            raise ValueError('n must be at least one')
        self = object.__new__(cls)
        self._it = iter(iterable)
        self._n = n
        self._strict = strict
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if self._it is None:
            raise StopIteration
        batch = []
        it = self._it
        for _ in range(self._n):
            try:
                batch.append(next(it))
            except StopIteration:
                self._it = None
                break
        if not batch:
            raise StopIteration
        if self._strict and len(batch) != self._n:
            self._it = None
            raise ValueError('batched(): incomplete batch')
        return tuple(batch)


class chain:
    """Return a chain object whose .__next__() method returns elements from the
first iterable until it is exhausted, then elements from the next
iterable, until all of the iterables are exhausted."""

    def __new__(cls, *iterables, **kwargs):
        if cls is chain:
            _no_keywords('chain', kwargs)
        self = object.__new__(cls)
        self._source = iter(iterables)
        self._active = None
        return self

    @classmethod
    def from_iterable(cls, iterable, /):
        """Alternative chain() constructor taking a single iterable argument that evaluates lazily."""
        self = object.__new__(cls)
        self._source = iter(iterable)
        self._active = None
        return self

    def __iter__(self):
        return self

    def __next__(self):
        while self._source is not None:
            if self._active is None:
                try:
                    iterable = next(self._source)
                except StopIteration:
                    self._source = None
                    break
                self._active = iter(iterable)
            try:
                return next(self._active)
            except StopIteration:
                self._active = None
        raise StopIteration

    def __class_getitem__(cls, item):
        return _GenericAlias(cls, item)


_GenericAlias = type(list[int])


class compress:
    """Return data elements corresponding to true selector elements.

Forms a shorter iterator from selected data elements using the selectors to
choose the data elements."""

    def __new__(cls, *args, **kwargs):
        (data, selectors), _ = _parse('compress', args, kwargs, ('data', 'selectors'), 2)
        self = object.__new__(cls)
        self._data = iter(data)
        self._selectors = iter(selectors)
        return self

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            value = next(self._data)
            if next(self._selectors):
                return value


class dropwhile:
    """Drop items from the iterable while predicate(item) is true.

Afterwards, return every element until the iterable is exhausted."""

    def __new__(cls, *args, **kwargs):
        if cls is dropwhile:
            _no_keywords('dropwhile', kwargs)
        _arity('dropwhile', args, 2)
        self = object.__new__(cls)
        self._predicate = args[0]
        self._it = iter(args[1])
        self._dropping = True
        return self

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            value = next(self._it)
            if not self._dropping:
                return value
            if not self._predicate(value):
                self._dropping = False
                return value


class takewhile:
    """Return successive entries from an iterable as long as the predicate evaluates to true for each entry."""

    def __new__(cls, *args, **kwargs):
        if cls is takewhile:
            _no_keywords('takewhile', kwargs)
        _arity('takewhile', args, 2)
        self = object.__new__(cls)
        self._predicate = args[0]
        self._it = iter(args[1])
        self._stopped = False
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if self._stopped:
            raise StopIteration
        value = next(self._it)
        if self._predicate(value):
            return value
        self._stopped = True
        raise StopIteration


class filterfalse:
    """Return those items of iterable for which function(item) is false.

If function is None, return the items that are false."""

    def __new__(cls, *args, **kwargs):
        if cls is filterfalse:
            _no_keywords('filterfalse', kwargs)
        _arity('filterfalse', args, 2)
        self = object.__new__(cls)
        self._predicate = args[0]
        self._it = iter(args[1])
        return self

    def __iter__(self):
        return self

    def __next__(self):
        predicate = self._predicate
        while True:
            value = next(self._it)
            if not (value if predicate is None or predicate is bool else predicate(value)):
                return value


class _grouper:
    def __init__(self, parent, key):
        self._parent = parent
        self._key = key

    def __iter__(self):
        return self

    def __next__(self):
        parent = self._parent
        if parent._group is not self:
            raise StopIteration
        if parent._current is _marker:
            parent._step()
        if parent._current is _marker or not parent._key_equal(self._key, parent._current_key):
            raise StopIteration
        value = parent._current
        parent._current = _marker
        return value


_marker = object()


class groupby:
    """make an iterator that returns consecutive keys and groups from the iterable

  iterable
    Elements to divide into groups according to the key function.
  key
    A function for computing the group category for each element.
    If the key function is not specified or is None, the element itself
    is used for grouping."""

    def __new__(cls, *args, **kwargs):
        (iterable, key), _ = _parse('groupby', args, kwargs, ('iterable', 'key'), 1)
        key = None if key is _missing else key
        self = object.__new__(cls)
        self._it = iter(iterable)
        self._keyfunc = key
        self._current = _marker
        self._current_key = _marker
        self._target_key = _marker
        self._group = None
        return self

    def __iter__(self):
        return self

    def _step(self):
        try:
            value = next(self._it)
        except StopIteration:
            self._current = _marker
            raise
        self._current_key = value if self._keyfunc is None else self._keyfunc(value)
        self._current = value

    @staticmethod
    def _key_equal(a, b):
        return a is b or a == b

    def __next__(self):
        self._group = None
        while True:
            if self._current is _marker:
                try:
                    self._step()
                except StopIteration:
                    self._current = _marker
                    raise
            if self._target_key is _marker or not self._key_equal(self._target_key, self._current_key):
                break
            self._current = _marker
        self._target_key = self._current_key
        group = _grouper(self, self._target_key)
        self._group = group
        return self._target_key, group


class islice:
    """islice(iterable, stop) --> islice object
islice(iterable, start, stop[, step]) --> islice object

Return an iterator whose next() method returns selected values from an
iterable.  If start is specified, will skip all preceding elements;
otherwise, start defaults to zero.  Step defaults to one.  If
specified as another value, step determines how many values are
skipped between successive calls.  Works like a slice() on a list
but returns an iterator."""

    def __new__(cls, *args, **kwargs):
        if cls is islice:
            _no_keywords('islice', kwargs)
        _arity('islice', args, 2, 4)
        iterable = args[0]
        start, stop, step = 0, None, 1
        if len(args) == 2:
            stop = cls._argument(args[1], 'Stop argument for islice() must be None or an integer: 0 <= x <= sys.maxsize.')
        else:
            start = cls._argument(args[1], 'Indices for islice() must be None or an integer: 0 <= x <= sys.maxsize.')
            stop = cls._argument(args[2], 'Stop argument for islice() must be None or an integer: 0 <= x <= sys.maxsize.')
            if start is None:
                start = 0
            if len(args) == 4:
                step = args[3]
                if step is not None:
                    try:
                        step = _index(step)
                    except TypeError:
                        step = -1
                    if not 1 <= step <= _maxsize:
                        raise ValueError('Step for islice() must be a positive integer or None.')
                else:
                    step = 1
        self = object.__new__(cls)
        self._it = iter(iterable)
        self._next = start
        self._stop = stop
        self._step = step
        self._count = 0
        return self

    @staticmethod
    def _argument(value, message):
        if value is None:
            return None
        try:
            value = _index(value)
        except TypeError:
            raise ValueError(message) from None
        if not 0 <= value <= _maxsize:
            raise ValueError(message)
        return value

    def __iter__(self):
        return self

    def __next__(self):
        it = self._it
        if it is None:
            raise StopIteration
        stop = self._stop
        while self._count < self._next:
            try:
                next(it)
            except StopIteration:
                self._it = None
                raise
            self._count += 1
        if stop is not None and self._count >= stop:
            self._it = None
            raise StopIteration
        try:
            value = next(it)
        except StopIteration:
            self._it = None
            raise
        self._count += 1
        old = self._next
        self._next += self._step
        if self._next > _maxsize or self._next < old:
            self._next = _maxsize
        if stop is not None and self._next > stop:
            self._next = stop
        return value


class pairwise:
    """Return an iterator of overlapping pairs taken from the input iterator.

    s -> (s0,s1), (s1,s2), (s2, s3), ..."""

    def __new__(cls, *args, **kwargs):
        if cls is pairwise:
            _no_keywords('pairwise', kwargs)
        _arity('pairwise', args, 1)
        self = object.__new__(cls)
        self._it = iter(args[0])
        self._old = _marker
        return self

    def __iter__(self):
        return self

    def __next__(self):
        it = self._it
        if it is None:
            raise StopIteration
        if self._old is _marker:
            try:
                self._old = next(it)
            except StopIteration:
                self._it = None
                raise
        try:
            new = next(it)
        except StopIteration:
            self._it = None
            self._old = _marker
            raise
        result = (self._old, new)
        self._old = new
        return result


class starmap:
    """Return an iterator whose values are returned from the function evaluated with an argument tuple taken from the given sequence."""

    def __new__(cls, *args, **kwargs):
        if cls is starmap:
            _no_keywords('starmap', kwargs)
        _arity('starmap', args, 2)
        self = object.__new__(cls)
        self._function = args[0]
        self._it = iter(args[1])
        return self

    def __iter__(self):
        return self

    def __next__(self):
        arguments = next(self._it)
        return self._function(*tuple(arguments))


class _tee_dataobject:
    # One link of the buffer shared by tee iterators; its value is read once.
    __slots__ = ('value', 'next')

    def __init__(self):
        self.value = _marker
        self.next = None


class _tee:
    """Iterator wrapped to make it copyable."""

    def __new__(cls, iterable, /):
        it = iter(iterable)
        if type(it) is _tee:
            return it.__copy__()
        self = object.__new__(cls)
        self._source = [it]
        self._link = _tee_dataobject()
        return self

    def __iter__(self):
        return self

    def __next__(self):
        link = self._link
        if link.next is None:
            source = self._source[0]
            if source is None:
                raise StopIteration
            try:
                value = next(source)
            except StopIteration:
                raise
            if link.next is None:
                link.value = value
                link.next = _tee_dataobject()
        value = link.value
        self._link = link.next
        return value

    def __copy__(self):
        copy = object.__new__(_tee)
        copy._source = self._source
        copy._link = self._link
        return copy


def tee(iterable, n=2, /):
    """Returns a tuple of n independent iterators."""
    n = _index(n)
    if n < 0:
        raise ValueError('n cannot be negative')
    it = iter(iterable)
    if n == 0:
        return ()
    copy = getattr(type(it), '__copy__', None)
    first = it if copy is not None else _tee(it)
    return (first,) + tuple(first.__copy__() for _ in range(n - 1))


class zip_longest:
    """Return a zip_longest object whose .__next__() method returns a tuple where
the i-th element comes from the i-th iterable argument.  The .__next__()
method continues until the longest iterable in the argument sequence
is exhausted and then it raises StopIteration.  When the shorter iterables
are exhausted, the fillvalue is substituted in their place.  The fillvalue
defaults to None or can be specified by a keyword argument."""

    def __new__(cls, *iterables, **kwargs):
        fillvalue = None
        if kwargs:
            if list(kwargs) != ['fillvalue']:
                raise TypeError('zip_longest() got an unexpected keyword argument')
            fillvalue = kwargs['fillvalue']
        self = object.__new__(cls)
        self._iterators = [iter(it) for it in iterables]
        self._active = len(self._iterators)
        self._fillvalue = fillvalue
        return self

    def __iter__(self):
        return self

    def __next__(self):
        iterators = self._iterators
        if not iterators or not self._active:
            raise StopIteration
        result = []
        for i, it in enumerate(iterators):
            if it is None:
                result.append(self._fillvalue)
                continue
            try:
                result.append(next(it))
            except StopIteration:
                self._active -= 1
                if not self._active:
                    raise
                iterators[i] = None
                result.append(self._fillvalue)
        return tuple(result)


class product:
    """Cartesian product of input iterables.  Equivalent to nested for-loops.

For example, product(A, B) returns the same as:  ((x,y) for x in A for y in B).
The leftmost iterators are in the outermost for-loop, so the output tuples
cycle in a manner similar to an odometer (with the rightmost element changing
on every iteration).

To compute the product of an iterable with itself, specify the number
of repetitions with the optional repeat keyword argument. For example,
product(A, repeat=4) means the same as product(A, A, A, A).

product('ab', range(3)) --> ('a',0) ('a',1) ('a',2) ('b',0) ('b',1) ('b',2)
product((0,1), (0,1), (0,1)) --> (0,0,0) (0,0,1) (0,1,0) (0,1,1) (1,0,0) ..."""

    def __new__(cls, *iterables, **kwargs):
        repeat = 1
        if kwargs:
            if list(kwargs) != ['repeat']:
                raise TypeError('product() got an unexpected keyword argument')
            repeat = _index(kwargs['repeat'])
            if repeat < 0:
                raise ValueError('repeat argument cannot be negative')
        pools = [tuple(pool) for pool in iterables] * repeat
        self = object.__new__(cls)
        self._pools = pools
        self._indices = None
        self._done = any(not pool for pool in pools)
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if self._done:
            raise StopIteration
        pools = self._pools
        if self._indices is None:
            self._indices = [0] * len(pools)
            return tuple(pool[0] for pool in pools)
        indices = self._indices
        for i in reversed(range(len(pools))):
            indices[i] += 1
            if indices[i] < len(pools[i]):
                break
            indices[i] = 0
        else:
            self._done = True
            raise StopIteration
        return tuple(pool[i] for pool, i in zip(pools, indices))


class combinations:
    """Return successive r-length combinations of elements in the iterable.

combinations(range(4), 3) --> (0,1,2), (0,1,3), (0,2,3), (1,2,3)"""

    def __new__(cls, *args, **kwargs):
        (iterable, r), _ = _parse('combinations', args, kwargs, ('iterable', 'r'), 2)
        pool = tuple(iterable)
        r = _index(r)
        if r < 0:
            raise ValueError('r cannot be negative')
        self = object.__new__(cls)
        self._pool = pool
        self._r = r
        self._indices = None
        self._done = r > len(pool)
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if self._done:
            raise StopIteration
        pool, r = self._pool, self._r
        if self._indices is None:
            self._indices = list(range(r))
            return tuple(pool[i] for i in self._indices)
        indices, n = self._indices, len(pool)
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            self._done = True
            raise StopIteration
        indices[i] += 1
        for j in range(i + 1, r):
            indices[j] = indices[j - 1] + 1
        return tuple(pool[i] for i in indices)


class combinations_with_replacement:
    """Return successive r-length combinations of elements in the iterable allowing individual elements to have successive repeats.

combinations_with_replacement('ABC', 2) --> ('A','A'), ('A','B'), ('A','C'), ('B','B'), ('B','C'), ('C','C')"""

    def __new__(cls, *args, **kwargs):
        (iterable, r), _ = _parse('combinations_with_replacement', args, kwargs, ('iterable', 'r'), 2)
        pool = tuple(iterable)
        r = _index(r)
        if r < 0:
            raise ValueError('r cannot be negative')
        self = object.__new__(cls)
        self._pool = pool
        self._r = r
        self._indices = None
        self._done = not pool and r > 0
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if self._done:
            raise StopIteration
        pool, r = self._pool, self._r
        if self._indices is None:
            self._indices = [0] * r
            return tuple(pool[i] for i in self._indices)
        indices, n = self._indices, len(pool)
        for i in reversed(range(r)):
            if indices[i] != n - 1:
                break
        else:
            self._done = True
            raise StopIteration
        indices[i:] = [indices[i] + 1] * (r - i)
        return tuple(pool[i] for i in indices)


class permutations:
    """Return successive r-length permutations of elements in the iterable.

permutations(range(3), 2) --> (0,1), (0,2), (1,0), (1,2), (2,0), (2,1)"""

    def __new__(cls, *args, **kwargs):
        (iterable, r), _ = _parse('permutations', args, kwargs, ('iterable', 'r'), 1)
        r = None if r is _missing else r
        pool = tuple(iterable)
        n = len(pool)
        if r is None:
            r = n
        else:
            if not isinstance(r, int):
                raise TypeError('Expected int as r')
            r = int(r)
            if r < 0:
                raise ValueError('r must be non-negative')
        self = object.__new__(cls)
        self._pool = pool
        self._r = r
        self._indices = list(range(n))
        self._cycles = list(range(n, n - r, -1))
        self._started = False
        self._done = r > n
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if self._done:
            raise StopIteration
        pool, r, indices, cycles = self._pool, self._r, self._indices, self._cycles
        n = len(pool)
        if not self._started:
            self._started = True
            return tuple(pool[i] for i in indices[:r])
        for i in reversed(range(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i + 1:] + indices[i:i + 1]
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                return tuple(pool[i] for i in indices[:r])
        self._done = True
        raise StopIteration


for _cls in (count, cycle, repeat, accumulate, batched, chain, compress, dropwhile, takewhile,
             filterfalse, groupby, _grouper, islice, pairwise, starmap, _tee, _tee_dataobject,
             zip_longest, product, combinations, combinations_with_replacement, permutations):
    _cls.__module__ = 'itertools'
del _cls
