/* CPython binding for the Small Python engine: a Runtime owns one SPYContext,
 * converts plain values in both directions, wraps everything else as Object,
 * and turns Python callables into spy native functions. */
#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "spy.h"
#include "spy-std.h"

#include <string.h>

enum { MAX_DEPTH = 200 };

typedef struct ObjectRef ObjectRef;
typedef struct {
    PyObject_HEAD
    SPYContext *ctx;
    PyObject *output;   /* Callable receiving printed text, or NULL for sys.stdout. */
    PyObject *loader;   /* Callable mapping a module name to source, or NULL. */
    PyObject *modules;  /* Registered module name -> members dict, source string, or both. */
    ObjectRef *objects; /* Live Object wrappers, released when the runtime closes. */
    int callbacks;      /* Host callbacks currently running. */
} Runtime;
typedef struct ObjectRef {
    PyObject_HEAD
    Runtime *runtime;
    SPYValue *value;
    struct ObjectRef *prev, *next;
} Object;

static PyTypeObject RuntimeType, ObjectType;
static PyObject *Error;

static PyObject *to_python(Runtime *, SPYValue *, int);
static SPYValue *to_spy(Runtime *, PyObject *, int);

/* Errors from the engine become smallpython.Error with the exception's type
 * name, message, location, and the exception object itself. */
static PyObject *raise_spy_error(Runtime *rt) {
    SPYContext *c = rt->ctx;
    SPYValue *value = spy_error_value(c);
    PyObject *exception = value ? to_python(rt, value, 0) : Py_NewRef(Py_None);
    spy_release(value);
    if (!exception) { PyErr_Clear(); exception = Py_NewRef(Py_None); }
    PyObject *args = Py_BuildValue("(ssO)", spy_error_type(c), spy_error_display(c), exception);
    PyObject *error = args ? PyObject_Call(Error, args, NULL) : NULL;
    Py_XDECREF(args);
    if (error) {
        PyObject *filename = PyUnicode_FromString(spy_error_filename(c)), *line = PyLong_FromSize_t(spy_error_line(c));
        if (filename && line) {
            PyObject_SetAttrString(error, "filename", filename);
            PyObject_SetAttrString(error, "lineno", line);
        }
        Py_XDECREF(filename); Py_XDECREF(line);
    }
    spy_clear_error(c);
    Py_DECREF(exception);
    if (error) { PyErr_SetObject(Error, error); Py_DECREF(error); }
    return NULL;
}

/* A Python exception raised inside a host callback becomes the engine's
 * exception of the nearest builtin class with the same name, or RuntimeError.
 * An Error from the engine re-raises its original exception. */
static SPYValue *raise_python_error(Runtime *rt) {
    SPYContext *c = rt->ctx;
    PyObject *exception = PyErr_GetRaisedException();
    if (!exception) return spy_error(c, "SystemError", "host callback failed without an exception");
    if (PyErr_GivenExceptionMatches(exception, Error)) {
        PyObject *original = PyObject_GetAttrString(exception, "exception");
        if (original && PyObject_TypeCheck(original, &ObjectType) && ((Object *)original)->value &&
            ((Object *)original)->runtime == rt) {
            spy_raise(c, ((Object *)original)->value);
            Py_DECREF(original); Py_DECREF(exception);
            return NULL;
        }
        Py_XDECREF(original); PyErr_Clear();
    }
    PyObject *message = PyObject_Str(exception);
    const char *text = message ? PyUnicode_AsUTF8(message) : NULL;
    if (!text) { PyErr_Clear(); text = ""; }
    SPYValue *cls = NULL;
    PyObject *mro = PyObject_GetAttrString((PyObject *)Py_TYPE(exception), "__mro__");
    for (Py_ssize_t i = 0; mro && i < PyTuple_GET_SIZE(mro) && !cls; i++) {
        const char *name = ((PyTypeObject *)PyTuple_GET_ITEM(mro, i))->tp_name;
        cls = spy_get_global(c, name);
        if (cls && spy_type(cls) != SPY_CLASS) { spy_release(cls); cls = NULL; }
        if (!cls) spy_clear_error(c);
    }
    if (!mro) PyErr_Clear();
    Py_XDECREF(mro);
    /* The exception's args carry over when they convert; otherwise its message. */
    PyObject *args = PyObject_GetAttrString(exception, "args");
    Py_ssize_t n = args && PyTuple_Check(args) ? PyTuple_GET_SIZE(args) : -1;
    SPYValue **argv = PyMem_Calloc(n > 0 ? (size_t)n : 1, sizeof(*argv)), *error = NULL;
    for (Py_ssize_t i = 0; argv && i < n; i++)
        if (!(argv[i] = to_spy(rt, PyTuple_GET_ITEM(args, i), 0))) {
            while (i--) { spy_release(argv[i]); argv[i] = NULL; }
            n = -1;
            break;
        }
    PyErr_Clear(); spy_clear_error(c);
    if (cls && argv && n >= 0) error = spy_call(c, cls, (size_t)n, argv);
    else if (cls && argv && (argv[0] = spy_string(c, text, strlen(text)))) error = spy_call(c, cls, 1, argv);
    if (error) spy_raise(c, error);
    else if (!spy_error_type(c)[0]) spy_error(c, "RuntimeError", text);
    for (Py_ssize_t i = 0; argv && i < (n > 0 ? n : 1); i++) spy_release(argv[i]);
    PyMem_Free(argv); spy_release(error); spy_release(cls);
    Py_XDECREF(args);
    Py_XDECREF(message); Py_DECREF(exception);
    return NULL;
}

static Object *object_new(Runtime *rt, SPYValue *value) {
    Object *o = PyObject_New(Object, &ObjectType);
    if (!o) { spy_release(value); return NULL; }
    o->runtime = (Runtime *)Py_NewRef((PyObject *)rt);
    o->value = value;
    o->prev = NULL; o->next = rt->objects;
    if (rt->objects) rt->objects->prev = o;
    rt->objects = o;
    return o;
}
static int closed(Runtime *rt) {
    if (rt->ctx) return 0;
    PyErr_SetString(PyExc_RuntimeError, "the runtime is closed");
    return 1;
}

/* Host callables become spy natives that own a reference to the callable. */
static void release_callable(void *data) { Py_DECREF((PyObject *)data); }
static SPYValue *host_call(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *keywords, void *data) {
    Runtime *rt = spy_get_opaque(c);
    PyObject *args = PyTuple_New((Py_ssize_t)argc), *kwargs = NULL, *result = NULL;
    for (size_t i = 0; args && i < argc; i++) {
        PyObject *item = to_python(rt, argv[i], 0);
        if (!item) { Py_CLEAR(args); break; }
        PyTuple_SET_ITEM(args, (Py_ssize_t)i, item);
    }
    if (args && keywords) {
        PyObject *converted = to_python(rt, keywords, 0);
        if (converted && PyDict_Check(converted)) kwargs = converted;
        else { Py_XDECREF(converted); if (!PyErr_Occurred()) PyErr_SetString(PyExc_TypeError, "keywords must be a dict"); Py_CLEAR(args); }
    }
    if (args) {
        rt->callbacks++;
        result = PyObject_Call((PyObject *)data, args, kwargs);
        rt->callbacks--;
    }
    Py_XDECREF(args); Py_XDECREF(kwargs);
    if (!result) return raise_python_error(rt);
    SPYValue *value = to_spy(rt, result, 0);
    Py_DECREF(result);
    return value ? value : raise_python_error(rt);
}
static SPYValue *native_function(Runtime *rt, PyObject *callable, const char *fallback) {
    PyObject *name = PyObject_GetAttrString(callable, "__name__");
    const char *text = name && PyUnicode_Check(name) ? PyUnicode_AsUTF8(name) : NULL;
    if (!text) { PyErr_Clear(); text = fallback; }
    SPYValue *native = spy_native(rt->ctx, text, host_call, Py_NewRef(callable), release_callable);
    Py_XDECREF(name);
    return native;
}

/* Call a builtin by name with converted arguments, for types the C API has no
 * constructor for. Steals nothing; returns an owned value or NULL with a spy error. */
static SPYValue *call_builtin(SPYContext *c, const char *name, size_t argc, SPYValue *const *argv) {
    SPYValue *fn = spy_get_global(c, name), *result = fn ? spy_call(c, fn, argc, argv) : NULL;
    spy_release(fn);
    return result;
}

/* Python -> spy. Returns an owned value, or NULL with a Python exception set. */
static SPYValue *to_spy(Runtime *rt, PyObject *obj, int depth) {
    SPYContext *c = rt->ctx;
    SPYValue *v = NULL;
    if (depth > MAX_DEPTH) { PyErr_SetString(PyExc_RecursionError, "value is too deeply nested to convert"); return NULL; }
    if (obj == Py_None) v = spy_none(c);
    else if (PyBool_Check(obj)) v = spy_bool(c, obj == Py_True);
    else if (PyLong_CheckExact(obj) || (PyLong_Check(obj) && !PyBool_Check(obj))) {
        int overflow = 0;
        long long n = PyLong_AsLongLongAndOverflow(obj, &overflow);
        if (n == -1 && PyErr_Occurred()) return NULL;
        if (!overflow) v = spy_int(c, n);
        else {
            PyObject *text = PyObject_Str(obj);
            Py_ssize_t len;
            const char *s = text ? PyUnicode_AsUTF8AndSize(text, &len) : NULL;
            SPYValue *string = s ? spy_string(c, s, (size_t)len) : NULL;
            v = string ? call_builtin(c, "int", 1, &string) : NULL;
            spy_release(string); Py_XDECREF(text);
            if (!s) return NULL;
        }
    } else if (PyFloat_Check(obj)) v = spy_float(c, PyFloat_AS_DOUBLE(obj));
    else if (PyComplex_Check(obj)) {
        SPYValue *parts[] = {spy_float(c, PyComplex_RealAsDouble(obj)), spy_float(c, PyComplex_ImagAsDouble(obj))};
        v = parts[0] && parts[1] ? call_builtin(c, "complex", 2, parts) : NULL;
        spy_release(parts[0]); spy_release(parts[1]);
    } else if (PyUnicode_Check(obj)) {
        PyObject *bytes = PyUnicode_AsEncodedString(obj, "utf-8", "surrogatepass");
        if (!bytes) return NULL;
        v = spy_string(c, PyBytes_AS_STRING(bytes), (size_t)PyBytes_GET_SIZE(bytes));
        Py_DECREF(bytes);
    } else if (PyBytes_Check(obj)) v = spy_bytes(c, PyBytes_AS_STRING(obj), (size_t)PyBytes_GET_SIZE(obj));
    else if (PyByteArray_Check(obj)) {
        SPYValue *bytes = spy_bytes(c, PyByteArray_AS_STRING(obj), (size_t)PyByteArray_GET_SIZE(obj));
        v = bytes ? call_builtin(c, "bytearray", 1, &bytes) : NULL;
        spy_release(bytes);
    } else if (PyList_Check(obj) || PyTuple_Check(obj) || PyAnySet_Check(obj)) {
        PyObject *items = PySequence_Fast(obj, "expected a sequence");
        if (!items) return NULL;
        Py_ssize_t n = PySequence_Fast_GET_SIZE(items);
        SPYValue **converted = PyMem_Calloc(n ? (size_t)n : 1, sizeof(*converted));
        int failed = !converted;
        for (Py_ssize_t i = 0; !failed && i < n; i++)
            failed = !(converted[i] = to_spy(rt, PySequence_Fast_GET_ITEM(items, i), depth + 1));
        if (!failed) {
            if (PyTuple_Check(obj)) v = spy_tuple(c, (size_t)n, converted);
            else {
                SPYValue *list = spy_list(c);
                for (Py_ssize_t i = 0; list && i < n; i++)
                    if (spy_list_append(c, list, converted[i])) { spy_release(list); list = NULL; }
                if (list && PyAnySet_Check(obj)) {
                    v = call_builtin(c, PyFrozenSet_Check(obj) ? "frozenset" : "set", 1, &list);
                    spy_release(list);
                } else v = list;
            }
        }
        for (Py_ssize_t i = 0; converted && i < n; i++) spy_release(converted[i]);
        PyMem_Free(converted); Py_DECREF(items);
        if (failed) { if (!PyErr_Occurred()) PyErr_NoMemory(); return NULL; }
    } else if (PyDict_Check(obj)) {
        v = spy_dict(c);
        PyObject *key, *item;
        Py_ssize_t at = 0;
        while (v && PyDict_Next(obj, &at, &key, &item)) {
            SPYValue *k = to_spy(rt, key, depth + 1), *i = k ? to_spy(rt, item, depth + 1) : NULL;
            int failed = !i || spy_set_item(c, v, k, i);
            spy_release(k); spy_release(i);
            if (failed) {
                spy_release(v);
                if (PyErr_Occurred()) return NULL;
                return (SPYValue *)raise_spy_error(rt);
            }
        }
    } else if (PyObject_TypeCheck(obj, &ObjectType)) {
        Object *o = (Object *)obj;
        if (o->runtime != rt || !o->value) {
            PyErr_SetString(PyExc_ValueError, "the object belongs to another or a closed runtime");
            return NULL;
        }
        v = spy_retain(o->value);
    } else if (PyCallable_Check(obj)) v = native_function(rt, obj, "<host function>");
    else {
        PyErr_Format(PyExc_TypeError, "cannot convert '%.200s' to a Small Python value", Py_TYPE(obj)->tp_name);
        return NULL;
    }
    if (!v) return (SPYValue *)raise_spy_error(rt);
    return v;
}

/* spy -> Python for plain data; anything else is wrapped as Object. Borrowed
 * input; returns a new reference or NULL with a Python exception set. */
static PyObject *to_python(Runtime *rt, SPYValue *v, int depth) {
    SPYContext *c = rt->ctx;
    if (depth > MAX_DEPTH) { PyErr_SetString(PyExc_RecursionError, "value is too deeply nested to convert"); return NULL; }
    switch (spy_type(v)) {
    case SPY_NONE: Py_RETURN_NONE;
    case SPY_BOOL: return PyBool_FromLong(spy_truth(v));
    case SPY_INT: {
        int64_t n;
        if (!spy_as_int(c, v, &n)) return PyLong_FromLongLong(n);
        spy_clear_error(c);
        SPYValue *text = spy_str(c, v);
        const char *s = text ? spy_as_string(c, text, NULL) : NULL;
        PyObject *result = s ? PyLong_FromString(s, NULL, 10) : NULL;
        spy_release(text);
        return s ? result : raise_spy_error(rt);
    }
    case SPY_FLOAT: {
        double d;
        return spy_as_float(c, v, &d) ? raise_spy_error(rt) : PyFloat_FromDouble(d);
    }
    case SPY_COMPLEX: {
        SPYValue *re = spy_get_attr(c, v, "real"), *im = re ? spy_get_attr(c, v, "imag") : NULL;
        double a, b;
        int failed = !im || spy_as_float(c, re, &a) || spy_as_float(c, im, &b);
        spy_release(re); spy_release(im);
        return failed ? raise_spy_error(rt) : PyComplex_FromDoubles(a, b);
    }
    case SPY_STRING: {
        size_t len;
        const char *s = spy_as_string(c, v, &len);
        return s ? PyUnicode_DecodeUTF8(s, (Py_ssize_t)len, "surrogatepass") : raise_spy_error(rt);
    }
    case SPY_BYTES: case SPY_BYTEARRAY: {
        size_t len;
        SPYValue *bytes = spy_type(v) == SPY_BYTES ? spy_retain(v) : call_builtin(c, "bytes", 1, &v);
        const unsigned char *s = bytes ? spy_as_bytes(c, bytes, &len) : NULL;
        PyObject *result = !s ? NULL : spy_type(v) == SPY_BYTES ? PyBytes_FromStringAndSize((const char *)s, (Py_ssize_t)len)
                                                               : PyByteArray_FromStringAndSize((const char *)s, (Py_ssize_t)len);
        spy_release(bytes);
        return s ? result : raise_spy_error(rt);
    }
    case SPY_LIST: case SPY_TUPLE: case SPY_SET: case SPY_FROZENSET: case SPY_DICT: {
        int type = spy_type(v);
        PyObject *items = PyList_New(0), *result = NULL;
        SPYValue *iterator = items ? spy_iter(c, v) : NULL, *item;
        if (items && !iterator) { Py_DECREF(items); return raise_spy_error(rt); }
        int failed = !items;
        while (!failed && (item = spy_next(c, iterator))) {
            PyObject *key = to_python(rt, item, depth + 1), *value = NULL;
            if (key && type == SPY_DICT) {
                SPYValue *found = spy_get_item(c, v, item);
                value = found ? to_python(rt, found, depth + 1) : raise_spy_error(rt);
                spy_release(found);
                PyObject *pair = value ? PyTuple_Pack(2, key, value) : NULL;
                Py_DECREF(key); Py_XDECREF(value);
                key = pair;
            }
            spy_release(item);
            failed = !key || PyList_Append(items, key);
            Py_XDECREF(key);
        }
        spy_release(iterator);
        if (!failed && spy_error_type(c)[0]) { raise_spy_error(rt); failed = 1; }
        if (!failed) {
            if (type == SPY_LIST) result = Py_NewRef(items);
            else if (type == SPY_TUPLE) result = PyList_AsTuple(items);
            else if (type == SPY_SET) result = PySet_New(items);
            else if (type == SPY_FROZENSET) result = PyFrozenSet_New(items);
            else {
                result = PyDict_New();
                for (Py_ssize_t i = 0; result && i < PyList_GET_SIZE(items); i++) {
                    PyObject *pair = PyList_GET_ITEM(items, i);
                    if (PyDict_SetItem(result, PyTuple_GET_ITEM(pair, 0), PyTuple_GET_ITEM(pair, 1))) Py_CLEAR(result);
                }
            }
        }
        Py_XDECREF(items);
        return result;
    }
    default:
        return (PyObject *)object_new(rt, spy_retain(v));
    }
}

/* Output and module loading call back into Python. */
static int write_output(void *data, const char *s, size_t n) {
    Runtime *rt = data;
    PyObject *text = PyUnicode_DecodeUTF8(s, (Py_ssize_t)n, "surrogateescape"), *result = NULL;
    if (text) {
        if (rt->output) result = PyObject_CallOneArg(rt->output, text);
        else {
            PyObject *out = PySys_GetObject("stdout");
            result = out && out != Py_None ? PyObject_CallMethod(out, "write", "O", text) : Py_NewRef(Py_None);
        }
    }
    Py_XDECREF(text);
    if (!result) { PyErr_WriteUnraisable(NULL); return -1; }
    Py_DECREF(result);
    return 0;
}
static char *load_module(void *data, const char *name) {
    Runtime *rt = data;
    PyObject *source = PyObject_CallFunction(rt->loader, "s", name);
    char *copy = NULL;
    if (source && source != Py_None) {
        Py_ssize_t len;
        const char *s = PyUnicode_Check(source) ? PyUnicode_AsUTF8AndSize(source, &len) : NULL;
        if (s && (copy = malloc((size_t)len + 1))) memcpy(copy, s, (size_t)len + 1);
        else if (!s && !PyErr_Occurred()) PyErr_SetString(PyExc_TypeError, "a loader must return str or None");
    }
    if (PyErr_Occurred()) {
        raise_python_error(rt);
        free(copy); copy = NULL;
    }
    Py_XDECREF(source);
    return copy;
}
/* A module registered with Runtime.register_module: its members, then its source. */
static int init_module(SPYContext *c, SPYValue *module) {
    Runtime *rt = spy_get_opaque(c);
    SPYValue *name_value = spy_get_attr(c, module, "__name__");
    const char *name = name_value ? spy_as_string(c, name_value, NULL) : NULL;
    PyObject *spec = name ? PyDict_GetItemString(rt->modules, name) : NULL;
    spy_release(name_value);
    if (!spec) { if (!spy_error_type(c)[0]) spy_error(c, "ImportError", "module is not registered"); return -1; }
    PyObject *members = PyTuple_GET_ITEM(spec, 0), *source = PyTuple_GET_ITEM(spec, 1);
    PyObject *key, *value;
    Py_ssize_t at = 0;
    while (members != Py_None && PyDict_Next(members, &at, &key, &value)) {
        const char *attr = PyUnicode_AsUTF8(key);
        SPYValue *converted = attr ? to_spy(rt, value, 0) : NULL;
        int failed = !converted || spy_set_attr(c, module, attr, converted);
        spy_release(converted);
        if (failed) { if (PyErr_Occurred()) raise_python_error(rt); return -1; }
    }
    if (source == Py_None) return 0;
    PyObject *filename = PyUnicode_FromFormat("<%U>", PyTuple_GET_ITEM(spec, 2));
    const char *text = PyUnicode_AsUTF8(source), *file = filename ? PyUnicode_AsUTF8(filename) : NULL;
    int status = text && file ? spy_exec_module(c, module, text, file) : -1;
    Py_XDECREF(filename);
    if (PyErr_Occurred()) { raise_python_error(rt); status = -1; }
    return status;
}

/* Runtime */
static int Runtime_init(Runtime *self, PyObject *args, PyObject *kwargs) {
    static char *keywords[] = {"std", "step_limit", "output", "loader", NULL};
    int std = 1;
    Py_ssize_t step_limit = 0;
    PyObject *output = Py_None, *loader = Py_None;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|$pnOO", keywords, &std, &step_limit, &output, &loader)) return -1;
    if (self->ctx) { PyErr_SetString(PyExc_RuntimeError, "the runtime is already initialized"); return -1; }
    if (step_limit < 0) { PyErr_SetString(PyExc_ValueError, "step_limit must be >= 0"); return -1; }
    if ((output != Py_None && !PyCallable_Check(output)) || (loader != Py_None && !PyCallable_Check(loader))) {
        PyErr_SetString(PyExc_TypeError, "output and loader must be callable or None");
        return -1;
    }
    if (!(self->modules = PyDict_New())) return -1;
    if (!(self->ctx = spy_context_new())) { PyErr_NoMemory(); return -1; }
    spy_set_opaque(self->ctx, self);
    self->output = output == Py_None ? NULL : Py_NewRef(output);
    self->loader = loader == Py_None ? NULL : Py_NewRef(loader);
    spy_set_output(self->ctx, write_output, self);
    if (self->loader) spy_set_module_loader(self->ctx, load_module, self);
    spy_set_step_limit(self->ctx, (size_t)step_limit);
    if (std && spy_std_init(self->ctx)) { raise_spy_error(self); return -1; }
    return 0;
}
static void runtime_close(Runtime *self) {
    if (!self->ctx) return;
    for (Object *o = self->objects; o; o = o->next) { spy_release(o->value); o->value = NULL; }
    SPYContext *ctx = self->ctx;
    self->ctx = NULL;
    spy_context_free(ctx);
}
static void Runtime_dealloc(Runtime *self) {
    runtime_close(self);
    Py_XDECREF(self->output); Py_XDECREF(self->loader); Py_XDECREF(self->modules);
    Py_TYPE(self)->tp_free((PyObject *)self);
}
static PyObject *run_source(Runtime *self, PyObject *args, PyObject *kwargs, int evaluate) {
    static char *keywords[] = {"source", "filename", NULL};
    const char *source, *filename = "<string>";
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|s", keywords, &source, &filename) || closed(self)) return NULL;
    if (self->callbacks) {
        PyErr_SetString(PyExc_RuntimeError, "cannot evaluate source while a host function of this runtime is running");
        return NULL;
    }
    SPYValue *value = spy_eval(self->ctx, source, filename);
    if (!value) return raise_spy_error(self);
    PyObject *result = evaluate ? to_python(self, value, 0) : Py_NewRef(Py_None);
    spy_release(value);
    return result;
}
static PyObject *Runtime_eval(Runtime *self, PyObject *args, PyObject *kwargs) { return run_source(self, args, kwargs, 1); }
static PyObject *Runtime_exec(Runtime *self, PyObject *args, PyObject *kwargs) { return run_source(self, args, kwargs, 0); }
static PyObject *Runtime_getitem(Runtime *self, PyObject *key) {
    const char *name = PyUnicode_AsUTF8(key);
    if (!name || closed(self)) return NULL;
    SPYValue *value = spy_get_global(self->ctx, name);
    if (!value) {
        if (!strcmp(spy_error_type(self->ctx), "NameError")) { spy_clear_error(self->ctx); PyErr_SetObject(PyExc_KeyError, key); return NULL; }
        return raise_spy_error(self);
    }
    PyObject *result = to_python(self, value, 0);
    spy_release(value);
    return result;
}
static int Runtime_setitem(Runtime *self, PyObject *key, PyObject *item) {
    const char *name = PyUnicode_AsUTF8(key);
    if (!name || closed(self)) return -1;
    if (!item) {
        SPYValue *globals = spy_eval(self->ctx, "globals()", "<host>"), *k = globals ? spy_string(self->ctx, name, strlen(name)) : NULL;
        SPYValue *pop = globals ? spy_get_attr(self->ctx, globals, "pop") : NULL, *removed = pop && k ? spy_call(self->ctx, pop, 1, &k) : NULL;
        spy_release(globals); spy_release(k); spy_release(pop);
        if (!removed) {
            if (!strcmp(spy_error_type(self->ctx), "KeyError")) { spy_clear_error(self->ctx); PyErr_SetObject(PyExc_KeyError, key); return -1; }
            raise_spy_error(self); return -1;
        }
        spy_release(removed);
        return 0;
    }
    SPYValue *value = to_spy(self, item, 0);
    if (!value) return -1;
    int status = spy_set_global(self->ctx, name, value);
    spy_release(value);
    if (status) { raise_spy_error(self); return -1; }
    return 0;
}
static PyObject *Runtime_call(Runtime *self, PyObject *args, PyObject *kwargs) {
    if (PyTuple_GET_SIZE(args) < 1) { PyErr_SetString(PyExc_TypeError, "call() needs a function or global name"); return NULL; }
    if (closed(self)) return NULL;
    PyObject *target = PyTuple_GET_ITEM(args, 0);
    SPYValue *fn = NULL;
    if (PyUnicode_Check(target)) {
        const char *name = PyUnicode_AsUTF8(target);
        if (!name) return NULL;
        if (!(fn = spy_get_global(self->ctx, name))) return raise_spy_error(self);
    } else if (!(fn = to_spy(self, target, 0))) return NULL;
    Py_ssize_t argc = PyTuple_GET_SIZE(args) - 1;
    SPYValue **argv = PyMem_Calloc(argc ? (size_t)argc : 1, sizeof(*argv)), *keywords = NULL, *result = NULL;
    int failed = !argv;
    for (Py_ssize_t i = 0; !failed && i < argc; i++) failed = !(argv[i] = to_spy(self, PyTuple_GET_ITEM(args, i + 1), 0));
    if (!failed && kwargs && PyDict_GET_SIZE(kwargs)) failed = !(keywords = to_spy(self, kwargs, 0));
    if (!failed) result = spy_call_keywords(self->ctx, fn, (size_t)argc, argv, keywords);
    for (Py_ssize_t i = 0; argv && i < argc; i++) spy_release(argv[i]);
    PyMem_Free(argv); spy_release(keywords); spy_release(fn);
    if (failed) { if (!PyErr_Occurred()) PyErr_NoMemory(); return NULL; }
    if (!result) return raise_spy_error(self);
    PyObject *converted = to_python(self, result, 0);
    spy_release(result);
    return converted;
}
static PyObject *Runtime_define(Runtime *self, PyObject *args) {
    const char *name;
    PyObject *callable;
    if (!PyArg_ParseTuple(args, "sO", &name, &callable) || closed(self)) return NULL;
    if (!PyCallable_Check(callable)) { PyErr_SetString(PyExc_TypeError, "define() needs a callable"); return NULL; }
    SPYValue *native = spy_native(self->ctx, name, host_call, Py_NewRef(callable), release_callable);
    int status = native ? spy_set_global(self->ctx, name, native) : -1;
    spy_release(native);
    if (status) return raise_spy_error(self);
    return Py_NewRef(callable);
}
static PyObject *Runtime_register_module(Runtime *self, PyObject *args, PyObject *kwargs) {
    static char *keywords[] = {"name", "members", "source", NULL};
    PyObject *name, *members = Py_None, *source = Py_None;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "U|OO", keywords, &name, &members, &source) || closed(self)) return NULL;
    if (members != Py_None && !PyDict_Check(members)) { PyErr_SetString(PyExc_TypeError, "members must be a dict"); return NULL; }
    if (source != Py_None && !PyUnicode_Check(source)) { PyErr_SetString(PyExc_TypeError, "source must be a str"); return NULL; }
    PyObject *copy = members == Py_None ? Py_NewRef(Py_None) : PyDict_Copy(members);
    for (Py_ssize_t at = 0, i = 0; copy && copy != Py_None && i < PyDict_GET_SIZE(copy); i++) {
        PyObject *key, *value;
        PyDict_Next(copy, &at, &key, &value);
        if (!PyUnicode_Check(key)) { PyErr_SetString(PyExc_TypeError, "member names must be str"); Py_CLEAR(copy); }
    }
    PyObject *spec = copy ? PyTuple_Pack(3, copy, source, name) : NULL;
    Py_XDECREF(copy);
    const char *text = spec ? PyUnicode_AsUTF8(name) : NULL;
    int failed = !text || PyDict_SetItem(self->modules, name, spec);
    Py_XDECREF(spec);
    if (failed) return NULL;
    if (spy_new_module(self->ctx, text, init_module)) return raise_spy_error(self);
    Py_RETURN_NONE;
}
static PyObject *Runtime_mount(Runtime *self, PyObject *args, PyObject *kwargs) {
    static char *keywords[] = {"directory", "path", "read_only", NULL};
    PyObject *directory, *encoded = NULL;
    const char *path = NULL;
    int read_only = 0;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|z$p", keywords, &directory, &path, &read_only) ||
        !PyUnicode_FSConverter(directory, &encoded))
        return NULL;
    int status = closed(self) ? -2 : spy_mount(self->ctx, PyBytes_AS_STRING(encoded), path, read_only ? SPY_MOUNT_READ_ONLY : 0);
    Py_DECREF(encoded);
    if (status == -2) return NULL;
    if (status) return raise_spy_error(self);
    Py_RETURN_NONE;
}
static PyObject *Runtime_collect(Runtime *self, PyObject *unused) {
    (void)unused;
    return closed(self) ? NULL : PyLong_FromSize_t(spy_collect(self->ctx));
}
static PyObject *Runtime_close(Runtime *self, PyObject *unused) {
    (void)unused;
    if (self->callbacks) { PyErr_SetString(PyExc_RuntimeError, "cannot close a runtime from its own host function"); return NULL; }
    runtime_close(self);
    Py_RETURN_NONE;
}
static PyObject *Runtime_closed(Runtime *self, void *unused) { (void)unused; return PyBool_FromLong(!self->ctx); }
static PyMethodDef Runtime_methods[] = {
    {"eval", (PyCFunction)(void (*)(void))Runtime_eval, METH_VARARGS | METH_KEYWORDS, "eval(source, filename='<string>')\n\nRun source and return the value of its last expression."},
    {"exec", (PyCFunction)(void (*)(void))Runtime_exec, METH_VARARGS | METH_KEYWORDS, "exec(source, filename='<string>')\n\nRun source for its effects."},
    {"call", (PyCFunction)(void (*)(void))Runtime_call, METH_VARARGS | METH_KEYWORDS, "call(function, /, *args, **kwargs)\n\nCall a global by name, or an Object."},
    {"define", (PyCFunction)Runtime_define, METH_VARARGS, "define(name, function)\n\nBind a Python callable as a host function global."},
    {"register_module", (PyCFunction)(void (*)(void))Runtime_register_module, METH_VARARGS | METH_KEYWORDS,
     "register_module(name, members=None, source=None)\n\nRegister an importable module from members and Python source."},
    {"mount", (PyCFunction)(void (*)(void))Runtime_mount, METH_VARARGS | METH_KEYWORDS,
     "mount(directory, path=None, *, read_only=False)\n\nLet open() reach a host directory at an absolute path (default: its own)."},
    {"collect", (PyCFunction)Runtime_collect, METH_NOARGS, "Run the cycle collector; return the number of values freed."},
    {"close", (PyCFunction)Runtime_close, METH_NOARGS, "Free the engine context; wrapped Objects become unusable."},
    {0}
};
static PyGetSetDef Runtime_getset[] = {{"closed", (getter)Runtime_closed, NULL, "Whether the runtime is closed.", NULL}, {0}};
static PyMappingMethods Runtime_mapping = {0, (binaryfunc)Runtime_getitem, (objobjargproc)Runtime_setitem};
static PyTypeObject RuntimeType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "smallpython._core.Runtime",
    .tp_basicsize = sizeof(Runtime),
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_doc = "Runtime(*, std=True, step_limit=0, output=None, loader=None)\n\nAn independent Small Python engine context.",
    .tp_new = PyType_GenericNew,
    .tp_init = (initproc)Runtime_init,
    .tp_dealloc = (destructor)Runtime_dealloc,
    .tp_methods = Runtime_methods,
    .tp_getset = Runtime_getset,
    .tp_as_mapping = &Runtime_mapping,
};

/* Object: an engine value the binding does not copy. */
static SPYValue *live_value(Object *self) {
    if (self->value && self->runtime->ctx) return self->value;
    PyErr_SetString(PyExc_RuntimeError, "the runtime is closed");
    return NULL;
}
static void Object_dealloc(Object *self) {
    Runtime *rt = self->runtime;
    if (self->prev) self->prev->next = self->next;
    else rt->objects = self->next;
    if (self->next) self->next->prev = self->prev;
    if (self->value && rt->ctx) spy_release(self->value);
    Py_DECREF((PyObject *)rt);
    PyObject_Free(self);
}
static PyObject *Object_call(Object *self, PyObject *args, PyObject *kwargs) {
    if (!live_value(self)) return NULL;
    PyObject *full = PyTuple_New(PyTuple_GET_SIZE(args) + 1);
    if (!full) return NULL;
    PyTuple_SET_ITEM(full, 0, Py_NewRef((PyObject *)self));
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(args); i++) PyTuple_SET_ITEM(full, i + 1, Py_NewRef(PyTuple_GET_ITEM(args, i)));
    PyObject *result = Runtime_call(self->runtime, full, kwargs);
    Py_DECREF(full);
    return result;
}
static PyObject *Object_getattr(Object *self, PyObject *name) {
    PyObject *found = PyObject_GenericGetAttr((PyObject *)self, name);
    if (found || !PyErr_ExceptionMatches(PyExc_AttributeError)) return found;
    PyErr_Clear();
    const char *text = PyUnicode_AsUTF8(name);
    if (!text || !live_value(self)) return NULL;
    SPYValue *value = spy_get_attr(self->runtime->ctx, self->value, text);
    if (!value) {
        if (!strcmp(spy_error_type(self->runtime->ctx), "AttributeError")) {
            PyErr_SetString(PyExc_AttributeError, spy_error_message(self->runtime->ctx));
            spy_clear_error(self->runtime->ctx);
            return NULL;
        }
        return raise_spy_error(self->runtime);
    }
    PyObject *result = to_python(self->runtime, value, 0);
    spy_release(value);
    return result;
}
static int Object_setattr(Object *self, PyObject *name, PyObject *item) {
    const char *text = PyUnicode_AsUTF8(name);
    if (!text || !live_value(self)) return -1;
    if (!item) { PyErr_SetString(PyExc_TypeError, "cannot delete engine attributes from the host"); return -1; }
    SPYValue *value = to_spy(self->runtime, item, 0);
    int status = value ? spy_set_attr(self->runtime->ctx, self->value, text, value) : -1;
    spy_release(value);
    if (status && !PyErr_Occurred()) raise_spy_error(self->runtime);
    return status;
}
static PyObject *Object_getitem(Object *self, PyObject *key) {
    if (!live_value(self)) return NULL;
    SPYValue *k = to_spy(self->runtime, key, 0), *value = k ? spy_get_item(self->runtime->ctx, self->value, k) : NULL;
    spy_release(k);
    if (!value) return PyErr_Occurred() ? NULL : raise_spy_error(self->runtime);
    PyObject *result = to_python(self->runtime, value, 0);
    spy_release(value);
    return result;
}
static int Object_setitem(Object *self, PyObject *key, PyObject *item) {
    if (!live_value(self)) return -1;
    if (!item) { PyErr_SetString(PyExc_TypeError, "cannot delete engine items from the host"); return -1; }
    SPYValue *k = to_spy(self->runtime, key, 0), *value = k ? to_spy(self->runtime, item, 0) : NULL;
    int status = value ? spy_set_item(self->runtime->ctx, self->value, k, value) : -1;
    spy_release(k); spy_release(value);
    if (status && !PyErr_Occurred()) raise_spy_error(self->runtime);
    return status;
}
static PyObject *Object_iter(Object *self) {
    if (!live_value(self)) return NULL;
    SPYValue *iterator = spy_iter(self->runtime->ctx, self->value);
    if (!iterator) return raise_spy_error(self->runtime);
    return (PyObject *)object_new(self->runtime, iterator);
}
static PyObject *Object_next(Object *self) {
    if (!live_value(self)) return NULL;
    SPYValue *item = spy_next(self->runtime->ctx, self->value);
    if (!item) return spy_error_type(self->runtime->ctx)[0] ? raise_spy_error(self->runtime) : NULL;
    PyObject *result = to_python(self->runtime, item, 0);
    spy_release(item);
    return result;
}
static PyObject *Object_text(Object *self, int repr) {
    if (!live_value(self)) return NULL;
    SPYValue *text = repr ? spy_repr(self->runtime->ctx, self->value) : spy_str(self->runtime->ctx, self->value);
    if (!text) return raise_spy_error(self->runtime);
    PyObject *result = to_python(self->runtime, text, 0);
    spy_release(text);
    return result;
}
static PyObject *Object_repr(Object *self) { return self->value && self->runtime->ctx ? Object_text(self, 1) : PyUnicode_FromString("<smallpython.Object (closed)>"); }
static PyObject *Object_str(Object *self) { return Object_text(self, 0); }
static int Object_bool(Object *self) { return live_value(self) ? spy_truth(self->value) : -1; }
static PyNumberMethods Object_number = {.nb_bool = (inquiry)Object_bool};
static PyMappingMethods Object_mapping = {0, (binaryfunc)Object_getitem, (objobjargproc)Object_setitem};
static PyObject *Object_runtime(Object *self, void *unused) { (void)unused; return Py_NewRef((PyObject *)self->runtime); }
static PyGetSetDef Object_getset[] = {{"runtime", (getter)Object_runtime, NULL, "The runtime that owns this value.", NULL}, {0}};
static PyTypeObject ObjectType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "smallpython._core.Object",
    .tp_basicsize = sizeof(Object),
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = "A Small Python value that is not copied into a Python value.",
    .tp_dealloc = (destructor)Object_dealloc,
    .tp_call = (ternaryfunc)Object_call,
    .tp_getattro = (getattrofunc)Object_getattr,
    .tp_setattro = (setattrofunc)Object_setattr,
    .tp_as_mapping = &Object_mapping,
    .tp_as_number = &Object_number,
    .tp_iter = (getiterfunc)Object_iter,
    .tp_iternext = (iternextfunc)Object_next,
    .tp_repr = (reprfunc)Object_repr,
    .tp_str = (reprfunc)Object_str,
    .tp_getset = Object_getset,
};

static struct PyModuleDef module = {PyModuleDef_HEAD_INIT, "smallpython._core", "Small Python engine binding.", -1, NULL, NULL, NULL, NULL, NULL};
PyMODINIT_FUNC PyInit__core(void) {
    if (PyType_Ready(&RuntimeType) || PyType_Ready(&ObjectType)) return NULL;
    PyObject *m = PyModule_Create(&module);
    if (!m) return NULL;
    Error = PyErr_NewExceptionWithDoc("smallpython._core.Error",
        "An exception raised inside Small Python: args are (type, message, exception).", NULL, NULL);
    if (!Error || PyModule_AddObjectRef(m, "Error", Error) || PyModule_AddObjectRef(m, "Runtime", (PyObject *)&RuntimeType) ||
        PyModule_AddObjectRef(m, "Object", (PyObject *)&ObjectType) || PyModule_AddStringConstant(m, "SPY_VERSION", SPY_VERSION)) {
        Py_DECREF(m); return NULL;
    }
    return m;
}
