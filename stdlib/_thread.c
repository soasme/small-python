/* _thread: threads of Python code, each on a system thread of its own,
 * taking turns at one context (docs/threads.md). Built as it is, it is a C
 * module that a host links and registers with spy_new_module(c, "_thread",
 * spy_init__thread); built with -DSPY_SHARED_MODULE -shared, it is the
 * native module _thread.so (spy-module.h).
 *
 * One thread at a time holds the context, its turn. Turns are handed on in
 * the order threads asked for them, through one mutex, so whatever a thread
 * did to the context happens before the next one runs. A thread gives up
 * its turn when it waits for a lock, when it ends, and, while another thread
 * waits, between two steps once it has held the turn for SLICE. The
 * thread that registered the module, the host's, holds the turn whenever
 * the host is outside the engine, so other threads run only during the
 * host's calls. */
#if defined(__linux__)
#define _GNU_SOURCE
#elif defined(__APPLE__)
#define _DARWIN_C_SOURCE
#elif !defined(_WIN32)
#define _POSIX_C_SOURCE 200809L
#endif
#include "spy-module.h"

#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#if defined(_WIN32)
#include <windows.h>
#include <process.h>
typedef CRITICAL_SECTION Mutex;
typedef CONDITION_VARIABLE Cond;
static void mutex_init(Mutex *m) { InitializeCriticalSection(m); }
static void mutex_destroy(Mutex *m) { DeleteCriticalSection(m); }
static void lock_mutex(Mutex *m) { EnterCriticalSection(m); }
static void unlock_mutex(Mutex *m) { LeaveCriticalSection(m); }
static void cond_init(Cond *v) { InitializeConditionVariable(v); }
static void cond_destroy(Cond *v) { (void)v; }
static void cond_broadcast(Cond *v) { WakeAllConditionVariable(v); }
static void cond_wait_ms(Cond *v, Mutex *m, double ms) {
    SleepConditionVariableCS(v, m, ms < 0 ? INFINITE : ms > 4e9 ? 4000000000u : (DWORD)ms);
}
static uint64_t current_ident(void) { return GetCurrentThreadId(); }
static uint64_t native_ident(void) { return GetCurrentThreadId(); }
#else
#include <pthread.h>
#include <unistd.h>
#if defined(__linux__)
#include <sys/syscall.h>
#endif
typedef pthread_mutex_t Mutex;
typedef pthread_cond_t Cond;
static void mutex_init(Mutex *m) { pthread_mutex_init(m, NULL); }
static void mutex_destroy(Mutex *m) { pthread_mutex_destroy(m); }
static void lock_mutex(Mutex *m) { pthread_mutex_lock(m); }
static void unlock_mutex(Mutex *m) { pthread_mutex_unlock(m); }
static void cond_init(Cond *v) { pthread_cond_init(v, NULL); }
static void cond_destroy(Cond *v) { pthread_cond_destroy(v); }
static void cond_broadcast(Cond *v) { pthread_cond_broadcast(v); }
static void cond_wait_ms(Cond *v, Mutex *m, double ms) {
    if (ms < 0) { pthread_cond_wait(v, m); return; }
    struct timespec at;
    timespec_get(&at, TIME_UTC);
    long long ns = at.tv_nsec + (long long)((ms > 1e12 ? 1e12 : ms) * 1e6);
    at.tv_sec += (time_t)(ns / 1000000000LL); at.tv_nsec = (long)(ns % 1000000000LL);
    pthread_cond_timedwait(v, m, &at);
}
static uint64_t current_ident(void) { return (uint64_t)(uintptr_t)pthread_self(); }
static uint64_t native_ident(void) {
#if defined(__APPLE__)
    uint64_t id = 0;
    pthread_threadid_np(NULL, &id);
    return id;
#elif defined(__linux__)
    return (uint64_t)syscall(SYS_gettid);
#else
    return current_ident();
#endif
}
#endif

/* Milliseconds on a clock that does not go back, for slices and timeouts. */
static double now_ms(void) {
    struct timespec t;
#if defined(_WIN32)
    timespec_get(&t, TIME_UTC);
#else
    clock_gettime(CLOCK_MONOTONIC, &t);
#endif
    return (double)t.tv_sec * 1e3 + (double)t.tv_nsec / 1e6;
}

enum { SLICE_MS = 5 }; /* As CPython's default sys.getswitchinterval(). */

typedef struct Shared Shared;
/* A thread of Python code: the host's, or one this module started. */
typedef struct Thread {
    Shared *shared;
    SPYThread *state; /* Its state while another thread holds the turn. */
    SPYValue *run; /* What a started thread calls; owned until it ends. */
} Thread;
/* A lock, freed with its value, or with the module when a thread still
 * waits for it then. */
typedef struct Lock {
    Shared *shared;
    struct Lock *next; /* In shared->orphans once its value is freed. */
    int locked;
    size_t waiters;
} Lock;
/* The module's state, shared by its functions, locks and threads, and freed
 * when the last of them is: when the context is freed, since a running
 * thread keeps the module. */
struct Shared {
    SPYContext *c;
    Mutex mutex;
    Cond turn, changed; /* A turn was handed on; a lock was released or the module is closing. */
    uint64_t next_ticket, serving; /* The holder's ticket is serving. */
    Thread host, *current;
    double since; /* When the current thread took its turn. */
    size_t refs, live, systems; /* References; started threads alive; their system threads not yet gone. */
    size_t stack; /* stack_size(), 0 for the default. */
    uint64_t main_ident;
    int closing;
    Lock *orphans;
};

static void unref(Shared *s) {
    lock_mutex(&s->mutex);
    int last = !--s->refs;
    if (last) {
        /* The context is being freed: every other thread waits, and leaves. */
        s->closing = 1;
        cond_broadcast(&s->turn); cond_broadcast(&s->changed);
        while (s->systems) cond_wait_ms(&s->changed, &s->mutex, -1);
    }
    unlock_mutex(&s->mutex);
    if (!last) return;
    while (s->orphans) { Lock *l = s->orphans; s->orphans = l->next; free(l); }
    cond_destroy(&s->turn); cond_destroy(&s->changed); mutex_destroy(&s->mutex);
    free(s);
}
static void release_shared(void *data) { unref(data); }

/* A started thread whose module is closing ends without touching the
 * context, whose values go with it; called with the mutex held. */
static void leave_system(Shared *s, Thread *t) {
    free(t);
    s->systems--;
    cond_broadcast(&s->changed);
    unlock_mutex(&s->mutex);
#if defined(_WIN32)
    _endthreadex(0);
#else
    pthread_exit(NULL);
#endif
}
static void take_turn(Shared *s, Thread *t) {
    lock_mutex(&s->mutex);
    uint64_t ticket = s->next_ticket++;
    while (s->serving != ticket && !s->closing) cond_wait_ms(&s->turn, &s->mutex, -1);
    if (s->closing) leave_system(s, t);
    s->current = t; s->since = now_ms();
    unlock_mutex(&s->mutex);
    spy_thread_swap(s->c, t->state);
}
static void give_turn(Shared *s, Thread *t) {
    spy_thread_swap(s->c, t->state);
    lock_mutex(&s->mutex);
    s->serving++;
    cond_broadcast(&s->turn);
    unlock_mutex(&s->mutex);
}
/* The switch callback: another thread waits, and this one's slice is over. */
static void switch_turn(SPYContext *c, void *data) {
    (void)c;
    Shared *s = data;
    lock_mutex(&s->mutex);
    int other = s->next_ticket - s->serving > 1 && now_ms() - s->since >= SLICE_MS;
    unlock_mutex(&s->mutex);
    if (!other) return;
    Thread *t = s->current;
    give_turn(s, t);
    take_turn(s, t);
}

#if defined(_WIN32)
static unsigned __stdcall thread_main(void *data)
#else
static void *thread_main(void *data)
#endif
{
    Thread *t = data;
    Shared *s = t->shared;
    take_turn(s, t);
    SPYContext *c = s->c;
    SPYValue *result = spy_call(c, t->run, 0, NULL);
    if (!result) spy_clear_error(c);
    spy_release(result); spy_release(t->run);
    if (!--s->live) spy_set_switch(c, NULL, NULL);
    /* The turn passes on with a blank state; this one goes. */
    spy_thread_swap(c, t->state);
    spy_thread_free(c, t->state);
    free(t);
    lock_mutex(&s->mutex);
    s->serving++;
    s->systems--;
    cond_broadcast(&s->turn); cond_broadcast(&s->changed);
    unlock_mutex(&s->mutex);
    return 0;
}

static SPYValue *integer(SPYContext *c, uint64_t n) { return spy_int(c, (int64_t)n); }

/* _spawn(run): start a system thread calling run(), and return its ident. */
static SPYValue *spawn(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *keywords, void *data) {
    Shared *s = data;
    if (argc != 1 || keywords) return spy_error(c, "TypeError", "_spawn expects one argument");
    Thread *t = malloc(sizeof(*t));
    if (!t) return spy_error(c, "MemoryError", "allocation failed");
    t->shared = s; t->run = spy_retain(argv[0]);
    if (!(t->state = spy_thread_new(c))) { spy_release(t->run); free(t); return NULL; }
    /* Its C stack holds the engine's own allowance and some to spare. */
    size_t need = spy_get_limit(c, SPY_LIMIT_STACK) + (1u << 20), size = s->stack > need ? s->stack : need;
    lock_mutex(&s->mutex);
    s->systems++;
    unlock_mutex(&s->mutex);
    uint64_t ident = 0;
    int failed;
#if defined(_WIN32)
    unsigned id;
    uintptr_t handle = _beginthreadex(NULL, (unsigned)size, thread_main, t, 0, &id);
    failed = !handle;
    if (handle) { CloseHandle((HANDLE)handle); ident = id; }
#else
    pthread_t thread;
    pthread_attr_t attributes;
    failed = pthread_attr_init(&attributes) || pthread_attr_setstacksize(&attributes, size) ||
             pthread_attr_setdetachstate(&attributes, PTHREAD_CREATE_DETACHED);
    failed = failed || pthread_create(&thread, &attributes, thread_main, t);
    pthread_attr_destroy(&attributes);
    if (!failed) ident = (uint64_t)(uintptr_t)thread;
#endif
    if (failed) {
        lock_mutex(&s->mutex);
        s->systems--;
        unlock_mutex(&s->mutex);
        spy_thread_free(c, t->state); spy_release(t->run); free(t);
        return spy_error(c, "RuntimeError", "can't start new thread");
    }
    if (!s->live++) spy_set_switch(c, switch_turn, s);
    return integer(c, ident);
}

static void release_lock(void *data) {
    Lock *l = data;
    Shared *s = l->shared;
    lock_mutex(&s->mutex);
    int waited = l->waiters > 0;
    if (waited) { l->next = s->orphans; s->orphans = l; }
    unlock_mutex(&s->mutex);
    if (!waited) free(l);
    unref(s);
}
/* A lock's own function: (0, ms) acquires, waiting ms milliseconds at most
 * (forever when negative, not at all when zero); (1,) releases; (2,) tells
 * whether it is locked. */
static SPYValue *lock_call(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *keywords, void *data) {
    Lock *l = data;
    Shared *s = l->shared;
    int64_t op = -1;
    double ms = -1;
    if (keywords || !argc || spy_as_int(c, argv[0], &op) || op < 0 || op > 2 || (op == 0 && (argc != 2 || spy_as_float(c, argv[1], &ms))))
        return spy_error(c, "TypeError", "invalid lock operation");
    lock_mutex(&s->mutex);
    if (op == 1) {
        int was = l->locked;
        if (was) { l->locked = 0; cond_broadcast(&s->changed); }
        unlock_mutex(&s->mutex);
        return was ? spy_none(c) : spy_error(c, "RuntimeError", "release unlocked lock");
    }
    if (op == 2 || !l->locked || ms == 0) {
        int got = op == 0 && !l->locked;
        if (got) l->locked = 1;
        int answer = op == 2 ? l->locked : got;
        unlock_mutex(&s->mutex);
        return spy_bool(c, answer);
    }
    /* Wait without the turn, then take the lock, then a turn again. */
    l->waiters++;
    unlock_mutex(&s->mutex);
    Thread *t = s->current;
    give_turn(s, t);
    lock_mutex(&s->mutex);
    double end = ms < 0 ? 0 : now_ms() + ms;
    for (;;) {
        if (s->closing) leave_system(s, t);
        if (!l->locked) break;
        double left = ms < 0 ? -1 : end - now_ms();
        if (ms >= 0 && left <= 0) break;
        cond_wait_ms(&s->changed, &s->mutex, left);
    }
    int got = !l->locked;
    if (got) l->locked = 1;
    l->waiters--;
    unlock_mutex(&s->mutex);
    take_turn(s, t);
    return spy_bool(c, got);
}
static SPYValue *new_lock(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *keywords, void *data) {
    (void)argv;
    Shared *s = data;
    if (argc || keywords) return spy_error(c, "TypeError", "_lock takes no arguments");
    Lock *l = calloc(1, sizeof(*l));
    if (!l) return spy_error(c, "MemoryError", "allocation failed");
    l->shared = s;
    lock_mutex(&s->mutex);
    s->refs++;
    unlock_mutex(&s->mutex);
    return spy_native(c, "lock", lock_call, l, release_lock);
}

/* The functions of no state: idents, counts and the stack size. */
static SPYValue *query(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *keywords, void *data) {
    Shared *s = data;
    int64_t which = -1, size = 0;
    if (keywords || argc < 1 || argc > 2 || spy_as_int(c, argv[0], &which) || (argc == 2 && spy_as_int(c, argv[1], &size)))
        return spy_error(c, "TypeError", "invalid query");
    switch (which) {
    case 0: return integer(c, current_ident());
    case 1: return integer(c, native_ident());
    case 2: return integer(c, s->live);
    case 3: return integer(c, s->main_ident);
    default: {
        size_t old = s->stack;
        if (argc == 2) s->stack = (size_t)size;
        return integer(c, old);
    }
    }
}

/* The module in Python, a line at a time. */
static const char *const python[] = {
    "\"\"\"This module provides primitive operations to write multi-threaded programs.\n",
    "The 'threading' module provides a more convenient interface.\"\"\"\n",
    "error = RuntimeError\n",
    "TIMEOUT_MAX = 9223372036.0\n",
    "try:\n",
    "    from _spy import _setting\n",
    "except ImportError:\n",
    "    _setting = None\n",
    "\n",
    "def _report(error, message):\n",
    "    # As the engine reports an unraisable error: sys, loaded for its hook.\n",
    "    if _setting is None:\n",
    "        return\n",
    "    if _setting('unraisablehook') is None:\n",
    "        try:\n",
    "            import sys\n",
    "        except ImportError:\n",
    "            pass\n",
    "    hook = _setting('unraisablehook')\n",
    "    if hook is not None:\n",
    "        # The traceback starts in the thread's function, not in run.\n",
    "        if error.__traceback__ is not None:\n",
    "            error.__traceback__ = error.__traceback__.tb_next\n",
    "        hook(type(error), error, error.__traceback__, message, None)\n",
    "\n",
    "def _timeout(args, kwargs):\n",
    "    # acquire's arguments, as milliseconds to wait: negative for ever.\n",
    "    given = len(args) + len(kwargs)\n",
    "    if given > 2:\n",
    "        raise TypeError(f\"acquire() takes at most 2 arguments ({given} given)\")\n",
    "    values = dict(zip((\"blocking\", \"timeout\"), args))\n",
    "    for name in kwargs:\n",
    "        if name not in (\"blocking\", \"timeout\"):\n",
    "            raise TypeError(f\"acquire() got an unexpected keyword argument '{name}'\")\n",
    "        if name in values:\n",
    "            raise TypeError(f\"argument for acquire() given by name ('{name}') and position ({len(values)})\")\n",
    "        values[name] = kwargs[name]\n",
    "    blocking = bool(values.get(\"blocking\", True))\n",
    "    timeout = values.get(\"timeout\", -1)\n",
    "    kind = type(timeout)\n",
    "    if not (hasattr(kind, \"__float__\") or hasattr(kind, \"__index__\")):\n",
    "        raise TypeError(f\"must be real number, not {kind.__name__}\")\n",
    "    timeout = float(timeout)\n",
    "    if timeout != timeout:\n",
    "        raise ValueError(\"Invalid value NaN (not a number)\")\n",
    "    if not blocking:\n",
    "        if timeout != -1:\n",
    "            raise ValueError(\"can't specify a timeout for a non-blocking call\")\n",
    "        return 0.0\n",
    "    if timeout == -1:\n",
    "        return -1.0\n",
    "    if timeout < 0:\n",
    "        raise ValueError(\"timeout value must be a non-negative number\")\n",
    "    if timeout > TIMEOUT_MAX:\n",
    "        raise OverflowError(\"timestamp out of range for C PyTime_t\")\n",
    "    return timeout * 1000.0\n",
    "\n",
    "class lock:\n",
    "    \"\"\"A lock object is a synchronization primitive.\"\"\"\n",
    "    def __init__(self):\n",
    "        self._op = _lock()\n",
    "    def acquire(self, *args, **kwargs):\n",
    "        \"\"\"Lock the lock.\"\"\"\n",
    "        return self._op(0, _timeout(args, kwargs))\n",
    "    def release(self):\n",
    "        \"\"\"Release the lock.\"\"\"\n",
    "        self._op(1)\n",
    "    def locked(self):\n",
    "        \"\"\"Test whether the lock is currently locked.\"\"\"\n",
    "        return self._op(2)\n",
    "    def acquire_lock(self, *args, **kwargs):\n",
    "        \"\"\"An obsolete synonym of acquire().\"\"\"\n",
    "        return self._op(0, _timeout(args, kwargs))\n",
    "    def release_lock(self):\n",
    "        \"\"\"An obsolete synonym of release().\"\"\"\n",
    "        self._op(1)\n",
    "    def locked_lock(self):\n",
    "        \"\"\"An obsolete synonym of locked().\"\"\"\n",
    "        return self._op(2)\n",
    "    def __enter__(self):\n",
    "        return self._op(0, -1.0)\n",
    "    def __exit__(self, *args):\n",
    "        self._op(1)\n",
    "    def _at_fork_reinit(self):\n",
    "        self._op = _lock()\n",
    "    def __repr__(self):\n",
    "        state = 'locked' if self._op(2) else 'unlocked'\n",
    "        return f'<{state} _thread.lock object at {id(self):#x}>'\n",
    "LockType = lock\n",
    "\n",
    "def allocate_lock():\n",
    "    \"\"\"Create a new lock object. See help(type(threading.Lock())) for\n",
    "information about locks.\"\"\"\n",
    "    return lock()\n",
    "def allocate():\n",
    "    \"\"\"An obsolete synonym of allocate_lock().\"\"\"\n",
    "    return lock()\n",
    "\n",
    "class RLock:\n",
    "    \"\"\"A reentrant lock: the thread holding it may acquire it again.\"\"\"\n",
    "    def __init__(self, *args, **kwargs):\n",
    "        self._block = lock()\n",
    "        self._owner = 0\n",
    "        self._count = 0\n",
    "    def acquire(self, *args, **kwargs):\n",
    "        \"\"\"Lock the lock.\"\"\"\n",
    "        ms = _timeout(args, kwargs)\n",
    "        me = get_ident()\n",
    "        if self._count and self._owner == me:\n",
    "            self._count += 1\n",
    "            return True\n",
    "        if not self._block._op(0, ms):\n",
    "            return False\n",
    "        self._owner = me\n",
    "        self._count = 1\n",
    "        return True\n",
    "    __enter__ = acquire\n",
    "    def release(self):\n",
    "        \"\"\"Release the lock.\"\"\"\n",
    "        if not self._count or self._owner != get_ident():\n",
    "            raise RuntimeError('cannot release un-acquired lock')\n",
    "        self._count -= 1\n",
    "        if not self._count:\n",
    "            self._owner = 0\n",
    "            self._block.release()\n",
    "    def __exit__(self, *args):\n",
    "        self.release()\n",
    "    def locked(self):\n",
    "        \"\"\"Test whether the lock is currently locked.\"\"\"\n",
    "        return self._block.locked()\n",
    "    def _is_owned(self):\n",
    "        return bool(self._count) and self._owner == get_ident()\n",
    "    def _recursion_count(self):\n",
    "        return self._count if self._is_owned() else 0\n",
    "    def _release_save(self):\n",
    "        if not self._count:\n",
    "            raise RuntimeError('cannot release un-acquired lock')\n",
    "        state = (self._count, self._owner)\n",
    "        self._count = 0\n",
    "        self._owner = 0\n",
    "        self._block.release()\n",
    "        return state\n",
    "    def _acquire_restore(self, state):\n",
    "        self._block.acquire()\n",
    "        self._count, self._owner = state\n",
    "    def _at_fork_reinit(self):\n",
    "        self.__init__()\n",
    "    def __repr__(self):\n",
    "        state = 'locked' if self._block.locked() else 'unlocked'\n",
    "        return f'<{state} _thread.RLock object owner={self._owner} count={self._count} at {id(self):#x}>'\n",
    "\n",
    "def get_ident():\n",
    "    \"\"\"Return a non-zero integer that uniquely identifies the current thread\n",
    "amongst other threads that exist simultaneously.\"\"\"\n",
    "    return _query(0)\n",
    "\n",
    "def get_native_id():\n",
    "    \"\"\"Return a non-negative integer identifying the thread as reported\n",
    "by the OS (kernel).\"\"\"\n",
    "    return _query(1)\n",
    "\n",
    "def _count():\n",
    "    \"\"\"Return the number of currently running Python threads, excluding\n",
    "the main thread.\"\"\"\n",
    "    return _query(2)\n",
    "\n",
    "def _get_main_thread_ident():\n",
    "    return _query(3)\n",
    "\n",
    "def _is_main_interpreter():\n",
    "    return True\n",
    "\n",
    "def daemon_threads_allowed():\n",
    "    \"\"\"Return True if daemon threads are allowed in the current interpreter.\"\"\"\n",
    "    return True\n",
    "\n",
    "def stack_size(size=None, /):\n",
    "    \"\"\"Return the thread stack size used when creating new threads.\"\"\"\n",
    "    if size is None:\n",
    "        return _query(4)\n",
    "    size = size.__index__()\n",
    "    if size and size < 32768:\n",
    "        raise ValueError('size must be at least 32768 bytes')\n",
    "    if size < 0:\n",
    "        raise ValueError('size must be 0 or a positive value')\n",
    "    return _query(4, size)\n",
    "\n",
    "def exit():\n",
    "    \"\"\"This is synonymous to ``raise SystemExit''.\"\"\"\n",
    "    raise SystemExit\n",
    "def exit_thread():\n",
    "    \"\"\"An obsolete synonym of exit().\"\"\"\n",
    "    raise SystemExit\n",
    "\n",
    "def start_new_thread(function, args, kwargs=None, /):\n",
    "    \"\"\"Start a new thread and return its identifier.\"\"\"\n",
    "    if not callable(function):\n",
    "        raise TypeError('first arg must be callable')\n",
    "    if not isinstance(args, tuple):\n",
    "        raise TypeError('2nd arg must be a tuple')\n",
    "    if kwargs is not None and not isinstance(kwargs, dict):\n",
    "        raise TypeError('optional 3rd arg must be a dictionary')\n",
    "    def run():\n",
    "        try:\n",
    "            function(*args, **(kwargs or {}))\n",
    "        except SystemExit:\n",
    "            pass\n",
    "        except BaseException as error:\n",
    "            _report(error, f'Exception ignored in thread started by {function!r}')\n",
    "    return _spawn(run)\n",
    "def start_new(function, args, kwargs=None, /):\n",
    "    \"\"\"An obsolete synonym of start_new_thread().\"\"\"\n",
    "    return start_new_thread(function, args, kwargs)\n",
    "\n",
    "_handles = {}\n",
    "\n",
    "class _ThreadHandle:\n",
    "    def __init__(self):\n",
    "        self.ident = None\n",
    "        self._done = lock()\n",
    "        self._done.acquire()\n",
    "        self._daemon = True\n",
    "    def is_done(self):\n",
    "        return not self._done.locked()\n",
    "    def _set_done(self):\n",
    "        if self._done.locked():\n",
    "            self._done.release()\n",
    "    def join(self, timeout=None):\n",
    "        if self.ident == get_ident() and not self.is_done():\n",
    "            raise RuntimeError('Cannot join current thread')\n",
    "        if timeout is None or timeout < 0:\n",
    "            timeout = -1\n",
    "        if self._done.acquire(True, timeout):\n",
    "            self._done.release()\n",
    "    def __repr__(self):\n",
    "        return f'<_thread._ThreadHandle object: ident={self.ident}>'\n",
    "\n",
    "def start_joinable_thread(function, handle=None, daemon=True):\n",
    "    \"\"\"*For internal use only*: start a new thread.\"\"\"\n",
    "    if not callable(function):\n",
    "        raise TypeError('thread function must be callable')\n",
    "    if handle is None:\n",
    "        handle = _ThreadHandle()\n",
    "    handle._daemon = daemon\n",
    "    def run():\n",
    "        try:\n",
    "            function()\n",
    "        except SystemExit:\n",
    "            pass\n",
    "        except BaseException as error:\n",
    "            _report(error, f'Exception ignored in thread started by {function!r}')\n",
    "        finally:\n",
    "            _handles.pop(id(handle), None)\n",
    "            handle._set_done()\n",
    "    _handles[id(handle)] = handle\n",
    "    handle.ident = _spawn(run)\n",
    "    return handle\n",
    "\n",
    "def _make_thread_handle(ident):\n",
    "    handle = _ThreadHandle()\n",
    "    handle.ident = ident\n",
    "    return handle\n",
    "\n",
    "def _shutdown():\n",
    "    \"\"\"Wait for all non-daemon threads.\"\"\"\n",
    "    for handle in list(_handles.values()):\n",
    "        if not handle._daemon and handle.ident != get_ident():\n",
    "            handle.join()\n"};

static int define(SPYContext *c, SPYValue *module, Shared *s, const char *name, SPYNativeKeywords f) {
    SPYValue *v = spy_native(c, name, f, s, release_shared);
    if (!v) return -1;
    s->refs++;
    int status = spy_set_attr(c, module, name, v);
    spy_release(v);
    return status;
}
SPY_MODULE int spy_init__thread(SPYContext *c, SPYValue *module) {
    Shared *s = calloc(1, sizeof(*s));
    if (!s) { spy_error(c, "MemoryError", "allocation failed"); return -1; }
    s->c = c; s->next_ticket = 1; s->current = &s->host; s->host.shared = s; s->main_ident = current_ident();
    if (!(s->host.state = spy_thread_new(c))) { free(s); return -1; }
    mutex_init(&s->mutex); cond_init(&s->turn); cond_init(&s->changed);
    /* The module holds one reference until its functions are defined. */
    s->refs = 1;
    int status = define(c, module, s, "_spawn", spawn) || define(c, module, s, "_lock", new_lock) ||
                 define(c, module, s, "_query", query);
    unref(s);
    if (status) return -1;
    size_t len = 0, count = sizeof(python) / sizeof(*python);
    for (size_t i = 0; i < count; i++) len += strlen(python[i]);
    char *source = malloc(len + 1), *at = source;
    if (!source) { spy_error(c, "MemoryError", "allocation failed"); return -1; }
    for (size_t i = 0; i < count; i++) { size_t n = strlen(python[i]); memcpy(at, python[i], n); at += n; }
    *at = 0;
    status = spy_exec_module(c, module, source, "<frozen _thread>");
    free(source);
    return status;
}
