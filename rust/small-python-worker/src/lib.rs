//! Run untrusted Python from Rust.
//!
//! Each [`Runtime`] starts one `spy-worker` process, which owns a Small
//! Python context and seals itself under the operating system's sandbox
//! before it runs any code, and speaks the worker protocol
//! (docs/packaging/protocol.md) over its standard input and output. Values
//! cross by copy as [`Value`]; anything else stays in the worker and is
//! reached through an [`Object`] handle. A crash, a protocol violation, or
//! an expired timeout loses the worker, and the runtime with it.
//!
//! The worker executable is compiled by this crate's build script and
//! embedded in the program; on first use it is written to the user's cache
//! directory, unless [`Builder::worker`] names one.

use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::{self, Receiver, RecvTimeoutError, Sender};
use std::sync::{Arc, Mutex, OnceLock};
use std::time::{Duration, Instant};
use std::{fmt, fs, io, thread};

mod wire;

/// A value that crossed by copy, or a reference to one that stayed.
///
/// Only values whose engine type is exactly one of these come back by
/// content; instances of subclasses arrive as [`Value::Object`].
#[derive(Clone, Debug, PartialEq)]
pub enum Value {
    None,
    Bool(bool),
    Int(i64),
    /// An `int` beyond 64 bits, in the protocol's spelling: an optional
    /// `-`, then `0x` and lowercase hex digits.
    BigInt(String),
    Float(f64),
    Complex(f64, f64),
    /// A `str`; lone surrogates, which Rust cannot hold, arrive as U+FFFD.
    Str(String),
    Bytes(Vec<u8>),
    ByteArray(Vec<u8>),
    List(Vec<Value>),
    Tuple(Vec<Value>),
    Set(Vec<Value>),
    FrozenSet(Vec<Value>),
    Dict(Vec<(Value, Value)>),
    /// An engine value held by the worker.
    Object(Object),
    /// A host function, from [`Runtime::function`].
    Function(Function),
}

impl Value {
    pub fn as_bool(&self) -> Option<bool> {
        match self {
            Value::Bool(b) => Some(*b),
            _ => None,
        }
    }

    pub fn as_int(&self) -> Option<i64> {
        match self {
            Value::Int(n) => Some(*n),
            _ => None,
        }
    }

    pub fn as_float(&self) -> Option<f64> {
        match self {
            Value::Float(x) => Some(*x),
            _ => None,
        }
    }

    pub fn as_str(&self) -> Option<&str> {
        match self {
            Value::Str(s) => Some(s),
            _ => None,
        }
    }

    /// The items of a list or tuple.
    pub fn as_slice(&self) -> Option<&[Value]> {
        match self {
            Value::List(items) | Value::Tuple(items) => Some(items),
            _ => None,
        }
    }

    /// The value of the `str` key `key` of a dict.
    pub fn get(&self, key: &str) -> Option<&Value> {
        match self {
            Value::Dict(pairs) => pairs.iter().find(|(k, _)| k.as_str() == Some(key)).map(|(_, v)| v),
            _ => None,
        }
    }
}

macro_rules! from {
    ($($t:ty => $v:ident $(as $as:ty)?),*) => {$(
        impl From<$t> for Value {
            fn from(value: $t) -> Value {
                Value::$v(value $(as $as)?.into())
            }
        }
    )*};
}

from!(bool => Bool, i32 => Int, i64 => Int, u32 => Int, f64 => Float, &str => Str, String => Str,
      Vec<Value> => List, Object => Object, Function => Function);

impl From<()> for Value {
    fn from(_: ()) -> Value {
        Value::None
    }
}

impl<T: Into<Value>> From<Option<T>> for Value {
    fn from(value: Option<T>) -> Value {
        value.map_or(Value::None, Into::into)
    }
}

impl From<&Object> for Value {
    fn from(object: &Object) -> Value {
        Value::Object(object.clone())
    }
}

/// What a runtime shares with its objects: where they queue their release.
#[derive(Default)]
struct Shared {
    released: Mutex<Vec<u64>>,
    ended: AtomicBool,
}

/// A handle to an engine value held by the worker. Operate on it with the
/// runtime's methods. Clones share the handle, which the worker releases
/// with the next message after the last clone is dropped.
#[derive(Clone)]
pub struct Object(Arc<Handle>);

struct Handle {
    id: u64,
    shared: Arc<Shared>,
}

impl Object {
    fn new(id: u64, shared: &Arc<Shared>) -> Object {
        Object(Arc::new(Handle { id, shared: shared.clone() }))
    }
}

impl Drop for Handle {
    fn drop(&mut self) {
        if !self.shared.ended.load(Ordering::Acquire) {
            self.shared.released.lock().unwrap_or_else(|e| e.into_inner()).push(self.id);
        }
    }
}

/// Objects are equal when they are the same handle.
impl PartialEq for Object {
    fn eq(&self, other: &Object) -> bool {
        Arc::ptr_eq(&self.0, &other.0)
    }
}

impl fmt::Debug for Object {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Object({})", self.0.id)
    }
}

/// A host function registered with a runtime, as a value to pass into it.
#[derive(Clone)]
pub struct Function {
    id: u64,
    name: String,
    shared: Arc<Shared>,
}

impl PartialEq for Function {
    fn eq(&self, other: &Function) -> bool {
        self.id == other.id && Arc::ptr_eq(&self.shared, &other.shared)
    }
}

impl fmt::Debug for Function {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Function({:?})", self.name)
    }
}

/// An engine exception that escaped.
#[derive(Debug)]
pub struct PythonError {
    /// The class name, qualified by its module unless it is a builtin.
    pub type_name: String,
    /// The text CPython's traceback shows after the type.
    pub message: String,
    pub filename: String,
    pub line: i64,
    /// The exception itself, when the worker could send it.
    pub exception: Option<Object>,
    /// The host function's error the exception was raised for, if it
    /// escaped unchanged.
    pub cause: Option<Box<Error>>,
}

#[derive(Debug)]
pub enum Error {
    /// An engine exception escaped, or a host function raises one.
    Python(Box<PythonError>),
    /// The worker was lost: it crashed, broke the protocol, or was ended.
    /// `status` is its exit status, negative for a signal, or `None` when
    /// the parent terminated it.
    Worker { message: String, status: Option<i32> },
    /// An operation ran past the runtime's timeout; the worker was ended.
    Timeout(Duration),
    /// A host function failed with a Rust error; the engine sees a
    /// `RuntimeError` with its message.
    Host(Box<dyn std::error::Error + Send + Sync>),
    /// The runtime cannot do what was asked: it is closed, a value does not
    /// belong to it, or an argument is invalid.
    Invalid(String),
}

pub type Result<T, E = Error> = std::result::Result<T, E>;

impl Error {
    /// An exception for a host function to raise: the engine raises the
    /// builtin class `type_name`, or `RuntimeError` when there is none.
    pub fn python(type_name: impl Into<String>, message: impl Into<String>) -> Error {
        Error::Python(Box::new(PythonError {
            type_name: type_name.into(),
            message: message.into(),
            filename: String::new(),
            line: 0,
            exception: None,
            cause: None,
        }))
    }

    /// A Rust error for a host function to fail with.
    pub fn host(error: impl Into<Box<dyn std::error::Error + Send + Sync>>) -> Error {
        Error::Host(error.into())
    }

    /// The type name, for an engine exception.
    pub fn type_name(&self) -> Option<&str> {
        match self {
            Error::Python(e) => Some(&e.type_name),
            _ => None,
        }
    }

    /// Whether the runtime was lost with this error.
    pub fn is_lost(&self) -> bool {
        matches!(self, Error::Worker { .. } | Error::Timeout(_))
    }

    fn copy_lost(&self) -> Error {
        match self {
            Error::Worker { message, status } => Error::Worker { message: message.clone(), status: *status },
            Error::Timeout(timeout) => Error::Timeout(*timeout),
            _ => unreachable!("only a loss is copied"),
        }
    }
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Python(e) if e.message.is_empty() => f.write_str(&e.type_name),
            Error::Python(e) => write!(f, "{}: {}", e.type_name, e.message),
            Error::Worker { message, .. } | Error::Invalid(message) => f.write_str(message),
            Error::Timeout(timeout) => write!(f, "the operation exceeded the timeout of {timeout:?}"),
            Error::Host(e) => e.fmt(f),
        }
    }
}

impl std::error::Error for Error {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Error::Python(e) => e.cause.as_deref().map(|e| e as _),
            Error::Host(e) => e.source(),
            _ => None,
        }
    }
}

/// A host function: it receives the runtime, for nested requests, the
/// positional arguments, and the keyword arguments.
type HostFn = Arc<dyn Fn(&mut Runtime, Vec<Value>, Vec<(String, Value)>) -> Result<Value> + Send + Sync>;
type Output = Box<dyn FnMut(&str) + Send>;
type Loader = Box<dyn FnMut(&str) -> Option<String> + Send>;

/// The comparison of [`Runtime::compare`].
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Compare {
    Lt = 11,
    Le,
    Eq,
    Ne,
    Gt,
    Ge,
}

/// Options for a [`Runtime`].
pub struct Builder {
    std: bool,
    step_limit: u64,
    memory_limit: u64,
    timeout: Option<Duration>,
    message_limit: u32,
    output: Option<Output>,
    loader: Option<Loader>,
    worker: Option<PathBuf>,
}

impl Default for Builder {
    fn default() -> Builder {
        Builder {
            std: true,
            step_limit: 0,
            memory_limit: 0,
            timeout: None,
            message_limit: 64 << 20,
            output: None,
            loader: None,
            worker: None,
        }
    }
}

impl Builder {
    /// Register the standard modules (`sys`, `gc`, `weakref`, ...). Default on.
    pub fn std(mut self, std: bool) -> Builder {
        self.std = std;
        self
    }

    /// Evaluation steps per top-level `eval` or `exec`; 0 is unlimited.
    /// Exceeding it raises `RuntimeError` in the engine.
    pub fn step_limit(mut self, limit: u64) -> Builder {
        self.step_limit = limit;
        self
    }

    /// Bytes the engine may hold; 0 is unlimited. Exceeding it raises
    /// `MemoryError` in the engine.
    pub fn memory_limit(mut self, limit: u64) -> Builder {
        self.memory_limit = limit;
        self
    }

    /// Time one operation may spend running in the worker, host functions
    /// excluded. Exceeding it ends the worker with [`Error::Timeout`].
    pub fn timeout(mut self, timeout: Duration) -> Builder {
        self.timeout = Some(timeout);
        self
    }

    /// The largest message in bytes, either direction; 64 MiB by default.
    pub fn message_limit(mut self, limit: u32) -> Builder {
        self.message_limit = limit;
        self
    }

    /// Receives printed text; without it, text goes to standard output.
    pub fn output(mut self, output: impl FnMut(&str) + Send + 'static) -> Builder {
        self.output = Some(Box::new(output));
        self
    }

    /// Maps a module name to its source, or `None`. For `import pkg.mod` it
    /// is asked for `pkg.mod.__init__` (a package), then `pkg.mod`; source
    /// for `pkg.mod.__namespace__` makes a namespace package.
    pub fn loader(mut self, loader: impl FnMut(&str) -> Option<String> + Send + 'static) -> Builder {
        self.loader = Some(Box::new(loader));
        self
    }

    /// Run this worker executable instead of the embedded one.
    pub fn worker(mut self, path: impl Into<PathBuf>) -> Builder {
        self.worker = Some(path.into());
        self
    }

    /// Starts the worker and waits until it is ready.
    pub fn spawn(self) -> Result<Runtime> {
        if self.message_limit == 0 {
            return Err(Error::Invalid("message_limit must be at least 1".into()));
        }
        if self.timeout == Some(Duration::ZERO) {
            return Err(Error::Invalid("timeout must be positive".into()));
        }
        let path = match self.worker {
            Some(path) => path,
            None => embedded_worker()?,
        };
        let cannot = |e: io::Error| Error::Worker { message: format!("cannot start the worker: {e}"), status: None };
        let mut command = Command::new(&path);
        command.env_clear().current_dir("/").stdin(Stdio::piped()).stdout(Stdio::piped());
        #[cfg(unix)]
        std::os::unix::process::CommandExt::process_group(&mut command, 0);
        #[cfg(windows)]
        std::os::windows::process::CommandExt::creation_flags(&mut command, 0x200); // CREATE_NEW_PROCESS_GROUP
        let mut child = command.spawn().map_err(cannot)?;
        let to = writer(child.stdin.take().expect("piped stdin"));
        let from = reader(child.stdout.take().expect("piped stdout"), self.message_limit);
        let mut rt = Runtime {
            child,
            to: Some(to),
            from,
            shared: Arc::default(),
            lost: None,
            closed: false,
            timeout: self.timeout,
            deadline: None,
            message_limit: self.message_limit,
            functions: Vec::new(),
            output: self.output,
            loader: self.loader,
            failure: None,
            tokens: 0,
            depth: 0,
            callbacks: 0,
            version: String::new(),
        };
        let options = Value::Dict(vec![
            ("std".into(), self.std.into()),
            ("step_limit".into(), int(self.step_limit)),
            ("memory_limit".into(), int(self.memory_limit)),
            ("message_limit".into(), self.message_limit.into()),
        ]);
        match rt.run(wire::INIT, &[&options])? {
            Value::Str(version) => rt.version = version,
            _ => return Err(rt.violation("malformed version")),
        }
        Ok(rt)
    }
}

fn int(n: u64) -> Value {
    i64::try_from(n).map_or_else(|_| Value::BigInt(format!("{n:#x}")), Value::Int)
}

/// One Small Python engine in its own worker process.
///
/// While a host function runs, it receives the runtime and may make nested
/// requests ([`call`](Runtime::call), [`get`](Runtime::get), object
/// operations, ...), but not [`eval`](Runtime::eval) or
/// [`exec`](Runtime::exec).
pub struct Runtime {
    child: Child,
    to: Option<Sender<Vec<u8>>>,
    from: Receiver<Received>,
    shared: Arc<Shared>,
    lost: Option<Error>,
    closed: bool,
    timeout: Option<Duration>,
    deadline: Option<Instant>,
    message_limit: u32,
    functions: Vec<HostFn>,
    output: Option<Output>,
    loader: Option<Loader>,
    failure: Option<(u64, Error)>,
    tokens: u64,
    depth: usize,
    callbacks: usize,
    version: String,
}

impl Runtime {
    /// A runtime with the default options.
    pub fn new() -> Result<Runtime> {
        Builder::default().spawn()
    }

    pub fn builder() -> Builder {
        Builder::default()
    }

    /// The engine version the worker reported.
    pub fn version(&self) -> &str {
        &self.version
    }

    /// The worker's process id.
    pub fn id(&self) -> u32 {
        self.child.id()
    }

    /// Runs `source` and returns the value of its last expression statement.
    pub fn eval(&mut self, source: &str) -> Result<Value> {
        self.run(wire::EVAL, &[&source.into(), &"<string>".into()])
    }

    /// Runs `source` for its effects.
    pub fn exec(&mut self, source: &str) -> Result<()> {
        self.run(wire::EXEC, &[&source.into(), &"<string>".into()]).map(drop)
    }

    /// Calls `function`: a global name (`str`), an [`Object`], or a
    /// [`Function`].
    pub fn call(
        &mut self,
        function: impl Into<Value>,
        args: Vec<Value>,
        kwargs: Vec<(String, Value)>,
    ) -> Result<Value> {
        let kwargs = Value::Dict(kwargs.into_iter().map(|(k, v)| (k.into(), v)).collect());
        self.run(wire::CALL, &[&function.into(), &Value::Tuple(args), &kwargs])
    }

    /// Reads a global, falling back to builtins; `None` when absent.
    pub fn get(&mut self, name: &str) -> Result<Option<Value>> {
        match self.run(wire::GET, &[&name.into()]) {
            Err(e) if e.type_name() == Some("NameError") => Ok(None),
            result => result.map(Some),
        }
    }

    /// Sets a global.
    pub fn set(&mut self, name: &str, value: impl Into<Value>) -> Result<()> {
        self.run(wire::SET, &[&name.into(), &value.into()]).map(drop)
    }

    /// Deletes a global; a `KeyError` when absent.
    pub fn delete(&mut self, name: &str) -> Result<()> {
        self.run(wire::DELETE, &[&name.into()]).map(drop)
    }

    /// A host function as a value to pass into the engine, where it becomes
    /// a builtin function named `name`. The runtime keeps `f` until it ends.
    pub fn function<F>(&mut self, name: &str, f: F) -> Function
    where
        F: Fn(&mut Runtime, Vec<Value>, Vec<(String, Value)>) -> Result<Value> + Send + Sync + 'static,
    {
        self.functions.push(Arc::new(f));
        Function { id: self.functions.len() as u64, name: name.into(), shared: self.shared.clone() }
    }

    /// Binds a host function as the global `name`.
    pub fn define<F>(&mut self, name: &str, f: F) -> Result<()>
    where
        F: Fn(&mut Runtime, Vec<Value>, Vec<(String, Value)>) -> Result<Value> + Send + Sync + 'static,
    {
        let function = self.function(name, f);
        self.set(name, function)
    }

    /// Makes `import name` create a module whose attributes are `members`,
    /// then run `source` in it. Registering a name again replaces it.
    pub fn register_module(&mut self, name: &str, members: Vec<(String, Value)>, source: &str) -> Result<()> {
        let members = Value::Dict(members.into_iter().map(|(k, v)| (k.into(), v)).collect());
        self.run(wire::MODULE, &[&name.into(), &members, &source.into()]).map(drop)
    }

    /// Lets the engine's `open()` reach a host directory at the absolute
    /// engine path `path` (default: its resolved host path). Mounts are
    /// fixed once the worker has run code.
    pub fn mount(&mut self, directory: impl AsRef<Path>, path: Option<&str>, read_only: bool) -> Result<()> {
        let directory = directory.as_ref();
        let invalid = |why: &str| Error::Invalid(format!("cannot mount '{}': {why}", directory.display()));
        let resolved = fs::canonicalize(directory).map_err(|e| invalid(&e.to_string()))?;
        if !resolved.is_dir() {
            return Err(invalid("Not a directory"));
        }
        let resolved = resolved.to_str().ok_or_else(|| invalid("the path is not UTF-8"))?.to_owned();
        let path = path.map_or_else(|| resolved.clone(), str::to_owned);
        self.run(wire::MOUNT, &[&resolved.into(), &path.into(), &read_only.into()]).map(drop)
    }

    /// Runs the cycle collector; returns the number of values freed.
    pub fn collect(&mut self) -> Result<i64> {
        match self.run(wire::COLLECT, &[])? {
            Value::Int(n) => Ok(n),
            _ => Err(self.violation("malformed collect result")),
        }
    }

    /// `getattr(object, name)`
    pub fn getattr(&mut self, object: &Object, name: &str) -> Result<Value> {
        self.op(1, object, &[&name.into()])
    }

    /// `setattr(object, name, value)`
    pub fn setattr(&mut self, object: &Object, name: &str, value: impl Into<Value>) -> Result<()> {
        self.op(2, object, &[&name.into(), &value.into()]).map(drop)
    }

    /// `object[key]`
    pub fn get_item(&mut self, object: &Object, key: impl Into<Value>) -> Result<Value> {
        self.op(3, object, &[&key.into()])
    }

    /// `object[key] = value`
    pub fn set_item(&mut self, object: &Object, key: impl Into<Value>, value: impl Into<Value>) -> Result<()> {
        self.op(4, object, &[&key.into(), &value.into()]).map(drop)
    }

    /// `len(object)`
    pub fn len(&mut self, object: &Object) -> Result<i64> {
        let n = self.op(5, object, &[])?;
        n.as_int().ok_or_else(|| self.violation("malformed length"))
    }

    /// `item in object`
    pub fn contains(&mut self, object: &Object, item: impl Into<Value>) -> Result<bool> {
        let found = self.op(6, object, &[&item.into()])?;
        found.as_bool().ok_or_else(|| self.violation("malformed membership"))
    }

    /// `iter(object)`
    pub fn iter(&mut self, object: &Object) -> Result<Value> {
        self.op(7, object, &[])
    }

    /// `next(object)`, or `None` at the end.
    pub fn next(&mut self, object: &Object) -> Result<Option<Value>> {
        match self.op(8, object, &[]) {
            Err(e) if e.type_name() == Some("StopIteration") => Ok(None),
            result => result.map(Some),
        }
    }

    /// `bool(object)`
    pub fn truth(&mut self, object: &Object) -> Result<bool> {
        let truth = self.op(9, object, &[])?;
        truth.as_bool().ok_or_else(|| self.violation("malformed truth"))
    }

    /// `hash(object)`
    pub fn hash(&mut self, object: &Object) -> Result<i64> {
        let hash = self.op(10, object, &[])?;
        hash.as_int().ok_or_else(|| self.violation("malformed hash"))
    }

    /// `object < other` and the other rich comparisons.
    pub fn compare(&mut self, object: &Object, op: Compare, other: impl Into<Value>) -> Result<Value> {
        self.op(op as i64, object, &[&other.into()])
    }

    /// `repr(object)`
    pub fn repr(&mut self, object: &Object) -> Result<String> {
        match self.op(17, object, &[])? {
            Value::Str(s) => Ok(s),
            _ => Err(self.violation("malformed repr")),
        }
    }

    /// `str(object)`
    pub fn str(&mut self, object: &Object) -> Result<String> {
        match self.op(18, object, &[])? {
            Value::Str(s) => Ok(s),
            _ => Err(self.violation("malformed str")),
        }
    }

    /// `dir(object)`
    pub fn dir(&mut self, object: &Object) -> Result<Value> {
        self.op(19, object, &[])
    }

    /// Whether the runtime was closed or lost.
    pub fn is_closed(&self) -> bool {
        self.closed || self.lost.is_some()
    }

    /// Ends the worker: closes its input, waits a second for it to exit,
    /// and terminates it otherwise. Dropping a runtime terminates it at once.
    pub fn close(mut self) {
        self.closed = true;
        if self.lost.is_none() {
            drop(self.to.take());
            let _ = self.from.recv_timeout(Duration::from_secs(1));
            self.end();
        }
    }

    fn op(&mut self, op: i64, object: &Object, operands: &[&Value]) -> Result<Value> {
        let (op, target) = (Value::Int(op), Value::from(object));
        let mut fields = vec![&op, &target];
        fields.extend_from_slice(operands);
        self.run(wire::OP, &fields)
    }

    /// One request, top-level or nested; the timeout spans the top level.
    fn run(&mut self, kind: u8, fields: &[&Value]) -> Result<Value> {
        if let Some(lost) = &self.lost {
            return Err(lost.copy_lost());
        }
        if self.closed {
            return Err(Error::Invalid("the runtime is closed".into()));
        }
        if matches!(kind, wire::EVAL | wire::EXEC) && self.callbacks > 0 {
            return Err(Error::Invalid(
                "cannot evaluate source while a host function of this runtime is running".into(),
            ));
        }
        let top = self.depth == 0;
        if top {
            self.deadline = self.timeout.map(|timeout| Instant::now() + timeout);
        }
        self.depth += 1;
        let result = self.request(kind, fields);
        self.depth -= 1;
        if top {
            self.deadline = None;
        }
        result
    }

    fn request(&mut self, kind: u8, fields: &[&Value]) -> Result<Value> {
        let data = wire::message(kind, fields, &self.shared)?;
        if data.len() - 4 > self.message_limit as usize {
            return Err(Error::Invalid("message exceeds the limit".into()));
        }
        self.send(data)?;
        let reply = self.await_reply()?;
        let [value] = self.decode(&reply)?;
        if reply[0] == wire::RAISE {
            return Err(self.engine_error(value)?);
        }
        Ok(value)
    }

    fn await_reply(&mut self) -> Result<Vec<u8>> {
        loop {
            let message = self.receive()?;
            match message[0] {
                wire::RESULT | wire::RAISE => return Ok(message),
                wire::HOST | wire::LOAD | wire::OUTPUT => self.serve(&message)?,
                kind => return Err(self.violation(&format!("unexpected message kind {kind:#x}"))),
            }
        }
    }

    fn send(&mut self, data: Vec<u8>) -> Result<()> {
        let released = std::mem::take(&mut *self.shared.released.lock().unwrap_or_else(|e| e.into_inner()));
        let mut messages = vec![data];
        if !released.is_empty() {
            let ids = Value::Tuple(released.into_iter().map(int).collect());
            messages.insert(0, wire::message(wire::RELEASE, &[&ids], &self.shared)?);
        }
        for message in messages {
            let sent = self.to.as_ref().is_some_and(|to| to.send(message).is_ok());
            if !sent {
                return Err(self.exited());
            }
        }
        Ok(())
    }

    fn receive(&mut self) -> Result<Vec<u8>> {
        let received = match self.deadline {
            None => self.from.recv().map_err(|_| RecvTimeoutError::Disconnected),
            Some(deadline) => self.from.recv_timeout(deadline.saturating_duration_since(Instant::now())),
        };
        match received {
            Ok(Received::Message(message)) => Ok(message),
            Ok(Received::Violation(what)) => Err(self.violation(&what)),
            Ok(Received::End) | Err(RecvTimeoutError::Disconnected) => Err(self.exited()),
            Err(RecvTimeoutError::Timeout) => {
                let timeout = self.timeout.expect("a deadline has a timeout");
                Err(self.lose(Error::Timeout(timeout)))
            }
        }
    }

    fn decode<const N: usize>(&mut self, message: &[u8]) -> Result<[Value; N]> {
        let decoded = wire::Reader::new(message, &self.shared).values();
        decoded.map_err(|what| self.violation(&what))
    }

    // Losing the worker (protocol.md 8).

    fn violation(&mut self, what: &str) -> Error {
        self.lose(Error::Worker { message: format!("the worker broke the protocol: {what}"), status: None })
    }

    fn exited(&mut self) -> Error {
        let status = self.child.wait().ok();
        #[cfg(unix)]
        let signal = status.and_then(|s| std::os::unix::process::ExitStatusExt::signal(&s));
        #[cfg(not(unix))]
        let signal = None::<i32>;
        let (message, code) = match (signal, status.and_then(|s| s.code())) {
            (Some(signal), _) => (format!("the worker was killed by signal {signal}"), Some(-signal)),
            (None, Some(code)) => (format!("the worker exited with status {code}"), Some(code)),
            (None, None) => ("the worker ended".to_owned(), None),
        };
        self.lose(Error::Worker { message, status: code })
    }

    fn lose(&mut self, error: Error) -> Error {
        if self.lost.is_none() {
            self.lost = Some(error);
            self.end();
        }
        self.lost.as_ref().expect("lost").copy_lost()
    }

    fn end(&mut self) {
        self.shared.ended.store(true, Ordering::Release);
        drop(self.to.take());
        let _ = self.child.kill();
        let _ = self.child.wait();
        self.functions.clear();
        self.shared.released.lock().unwrap_or_else(|e| e.into_inner()).clear();
        self.failure = None;
        self.output = None;
        self.loader = None;
    }

    // Errors from the engine.

    fn engine_error(&mut self, error: Value) -> Result<Error> {
        let mut fields: [Option<Value>; 6] = Default::default();
        let keys = ["type", "message", "filename", "line", "exception", "token"];
        if let Value::Dict(pairs) = error {
            for (key, value) in pairs {
                match keys.iter().position(|k| key.as_str() == Some(k)) {
                    Some(i) if fields[i].is_none() => fields[i] = Some(value),
                    _ => return Err(self.violation("malformed error")),
                }
            }
        }
        let [Some(Value::Str(type_name)), Some(Value::Str(message)), Some(Value::Str(filename)), Some(Value::Int(line)), Some(exception @ (Value::Object(_) | Value::None)), Some(Value::Int(token))] =
            fields
        else {
            return Err(self.violation("malformed error"));
        };
        let cause = match self.failure.take() {
            Some((sent, cause)) if sent as i64 == token => Some(Box::new(cause)),
            _ => None,
        };
        let exception = match exception {
            Value::Object(object) => Some(object),
            _ => None,
        };
        Ok(Error::Python(Box::new(PythonError { type_name, message, filename, line, exception, cause })))
    }

    // Requests from the worker.

    fn serve(&mut self, message: &[u8]) -> Result<()> {
        let started = Instant::now();
        self.callbacks += 1;
        let result = self.dispatch(message);
        self.callbacks -= 1;
        if let Some(deadline) = &mut self.deadline {
            *deadline += started.elapsed();
        }
        if self.lost.is_some() {
            return Err(self.lost.as_ref().expect("lost").copy_lost());
        }
        let reply = match result? {
            Ok(value) => wire::message(wire::RESULT, &[&value], &self.shared),
            Err(error) => Err(error),
        };
        let reply = reply.and_then(|reply| {
            if reply.len() - 4 > self.message_limit as usize {
                Err(Error::Invalid("message exceeds the limit".into()))
            } else {
                Ok(reply)
            }
        });
        let reply = match reply {
            Ok(reply) => reply,
            Err(error) => {
                let failure = self.failure_of(error);
                wire::message(wire::RAISE, &[&failure], &self.shared)?
            }
        };
        self.send(reply)
    }

    /// The outer result is the protocol's; the inner one the callback's.
    fn dispatch(&mut self, message: &[u8]) -> Result<Result<Value>> {
        match message[0] {
            wire::HOST => {
                let [id, args, kwargs] = self.decode(message)?;
                let function = match id {
                    Value::Int(id) if id >= 1 => self.functions.get(id as usize - 1).cloned(),
                    _ => None,
                };
                let kwargs = match kwargs {
                    Value::Dict(pairs) => pairs
                        .into_iter()
                        .map(|(k, v)| match k {
                            Value::Str(k) => Some((k, v)),
                            _ => None,
                        })
                        .collect::<Option<Vec<_>>>(),
                    _ => None,
                };
                let (Some(function), Value::Tuple(args), Some(kwargs)) = (function, args, kwargs) else {
                    return Err(self.violation("malformed host call"));
                };
                // A panic leaves the worker mid-turn: lose it, then go on unwinding.
                let call = std::panic::AssertUnwindSafe(|| function(self, args, kwargs));
                match std::panic::catch_unwind(call) {
                    Ok(result) => Ok(result),
                    Err(panic) => {
                        self.lose(Error::Worker { message: "a host function panicked".into(), status: None });
                        std::panic::resume_unwind(panic)
                    }
                }
            }
            wire::LOAD => {
                let [Value::Str(name)] = self.decode(message)? else {
                    return Err(self.violation("malformed load"));
                };
                let source = self.loader.as_mut().and_then(|load| load(&name));
                Ok(Ok(source.into()))
            }
            _ => {
                let [Value::Str(text)] = self.decode(message)? else {
                    return Err(self.violation("malformed output"));
                };
                match &mut self.output {
                    Some(output) => output(&text),
                    None => {
                        if let Err(e) = io::stdout().write_all(text.as_bytes()) {
                            return Ok(Err(Error::python("OSError", e.to_string())));
                        }
                    }
                }
                Ok(Ok(Value::None))
            }
        }
    }

    /// The failure (protocol.md 7.4) for an error a callback returned.
    fn failure_of(&mut self, error: Error) -> Value {
        self.tokens += 1;
        let token = Value::Int(self.tokens as i64);
        let failure = match &error {
            Error::Python(e) if e.exception.as_ref().is_some_and(|x| Arc::ptr_eq(&x.0.shared, &self.shared)) => {
                vec![("raise".into(), Value::from(e.exception.as_ref().expect("exception"))), ("token".into(), token)]
            }
            _ => {
                let (classes, message) = match &error {
                    Error::Python(e) => (vec![e.type_name.as_str().into()], e.message.clone()),
                    Error::Invalid(message) => (vec!["ValueError".into()], message.clone()),
                    error => (vec!["RuntimeError".into()], error.to_string()),
                };
                vec![
                    ("classes".into(), Value::Tuple(classes)),
                    ("args".into(), Value::None),
                    ("message".into(), message.into()),
                    ("token".into(), token),
                ]
            }
        };
        self.failure = Some((self.tokens, error));
        Value::Dict(failure)
    }
}

impl Drop for Runtime {
    fn drop(&mut self) {
        if self.lost.is_none() {
            self.end();
        }
    }
}

/// What the reader thread passes on.
enum Received {
    Message(Vec<u8>),
    Violation(String),
    End,
}

/// Reads frames from the worker on a thread of its own, so the parent can
/// wait for them with a deadline. Lengths are checked before allocating.
fn reader(mut from: ChildStdout, limit: u32) -> Receiver<Received> {
    let (tx, rx) = mpsc::channel();
    thread::spawn(move || loop {
        let mut length = [0; 4];
        if from.read_exact(&mut length).is_err() {
            let _ = tx.send(Received::End);
            return;
        }
        let n = u32::from_le_bytes(length);
        if !(1..=limit).contains(&n) {
            let _ = tx.send(Received::Violation("message length out of range".into()));
            return;
        }
        let mut message = vec![0; n as usize];
        let received = match from.read_exact(&mut message) {
            Ok(()) => Received::Message(message),
            Err(_) => Received::End,
        };
        let end = !matches!(received, Received::Message(_));
        if tx.send(received).is_err() || end {
            return;
        }
    });
    rx
}

/// Writes to the worker on a thread of its own, so a worker that stops
/// reading cannot block the parent past its deadline.
fn writer(mut to: ChildStdin) -> Sender<Vec<u8>> {
    let (tx, rx) = mpsc::channel::<Vec<u8>>();
    thread::spawn(move || {
        for message in rx {
            if to.write_all(&message).is_err() {
                return;
            }
        }
    });
    tx
}

static WORKER: &[u8] = include_bytes!(concat!(env!("OUT_DIR"), "/spy-worker"));

/// The embedded worker, written once per version to the user's cache
/// directory and checked against the embedded bytes on first use.
fn embedded_worker() -> Result<PathBuf> {
    static PATH: OnceLock<Result<PathBuf, String>> = OnceLock::new();
    let path = PATH.get_or_init(|| install_worker().map_err(|e| format!("cannot install the worker: {e}")));
    path.clone().map_err(|message| Error::Worker { message, status: None })
}

fn install_worker() -> io::Result<PathBuf> {
    let digest = WORKER.iter().fold(0xcbf29ce484222325u64, |h, &b| (h ^ b as u64).wrapping_mul(0x100000001b3));
    let name = format!("spy-worker-{}-{digest:016x}{}", env!("CARGO_PKG_VERSION"), std::env::consts::EXE_SUFFIX);
    let dir = cache_dir().join("small-python");
    let path = dir.join(&name);
    if fs::read(&path).is_ok_and(|bytes| bytes == WORKER) {
        return Ok(path);
    }
    fs::create_dir_all(&dir)?;
    let partial = dir.join(format!("{name}.{}", std::process::id()));
    let mut options = fs::OpenOptions::new();
    options.write(true).create(true).truncate(true);
    #[cfg(unix)]
    std::os::unix::fs::OpenOptionsExt::mode(&mut options, 0o700);
    options.open(&partial)?.write_all(WORKER)?;
    fs::rename(&partial, &path)?;
    Ok(path)
}

fn cache_dir() -> PathBuf {
    let var = |name| std::env::var_os(name).map(PathBuf::from).filter(|p| p.is_absolute());
    let home = || var("HOME");
    if cfg!(windows) {
        var("LOCALAPPDATA")
    } else if cfg!(target_os = "macos") {
        home().map(|h| h.join("Library/Caches"))
    } else {
        var("XDG_CACHE_HOME").or_else(|| home().map(|h| h.join(".cache")))
    }
    .unwrap_or_else(std::env::temp_dir)
}
