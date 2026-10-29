use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

use small_python_worker::{Compare, Error, Runtime, Value};

fn int(n: i64) -> Value {
    Value::Int(n)
}

#[test]
fn evaluates_and_converts() {
    let mut rt = Runtime::new().unwrap();
    assert_eq!(rt.version(), small_python_worker_version());
    assert_eq!(rt.eval("6 * 7").unwrap(), int(42));
    assert_eq!(rt.eval("2 ** 64").unwrap(), Value::BigInt("0x10000000000000000".into()));
    assert_eq!(rt.eval("-2 ** 63").unwrap(), int(i64::MIN));
    assert_eq!(rt.eval("1j + 0.5").unwrap(), Value::Complex(0.5, 1.0));
    assert_eq!(rt.eval("'\\udc80x'").unwrap(), Value::from("\u{fffd}x"));
    assert_eq!(
        rt.eval("[None, True, b'a', bytearray(b'b'), (1,), {1: 'x'}, {2}, frozenset()]").unwrap(),
        Value::List(vec![
            Value::None,
            Value::Bool(true),
            Value::Bytes(b"a".to_vec()),
            Value::ByteArray(b"b".to_vec()),
            Value::Tuple(vec![int(1)]),
            Value::Dict(vec![(int(1), "x".into())]),
            Value::Set(vec![int(2)]),
            Value::FrozenSet(vec![]),
        ])
    );
    rt.set("big", Value::BigInt("-0x10000000000000000".into())).unwrap();
    assert_eq!(rt.eval("big == -2 ** 64").unwrap(), Value::Bool(true));
}

fn small_python_worker_version() -> String {
    let header = std::fs::read_to_string(concat!(env!("CARGO_MANIFEST_DIR"), "/../../spy.h")).unwrap();
    header.lines().find_map(|l| l.strip_prefix("#define SPY_VERSION \"")).unwrap().trim_end_matches('"').to_owned()
}

#[test]
fn globals() {
    let mut rt = Runtime::new().unwrap();
    rt.set("x", 1).unwrap();
    assert_eq!(rt.get("x").unwrap(), Some(int(1)));
    assert_eq!(rt.get("len").unwrap().map(|v| matches!(v, Value::Object(_))), Some(true));
    rt.delete("x").unwrap();
    assert_eq!(rt.get("x").unwrap(), None);
    assert_eq!(rt.delete("x").unwrap_err().type_name(), Some("KeyError"));
}

#[test]
fn exceptions_carry_their_place() {
    let mut rt = Runtime::new().unwrap();
    let Error::Python(e) = rt.exec("x = 1\nraise ValueError('bad')").unwrap_err() else { panic!() };
    assert_eq!((e.type_name.as_str(), e.message.as_str(), e.line), ("ValueError", "bad", 2));
    let exception = e.exception.unwrap();
    assert_eq!(rt.repr(&exception).unwrap(), "ValueError('bad')");
}

#[test]
fn host_functions_and_nested_requests() {
    let mut rt = Runtime::new().unwrap();
    rt.define("add", |_, args, kwargs| match (&args[..], &kwargs[..]) {
        ([Value::Int(a), Value::Int(b)], []) => Ok(Value::Int(a + b)),
        _ => Err(Error::python("TypeError", "add(a, b)")),
    })
    .unwrap();
    // Recursion through the engine and back, several levels deep.
    rt.define("down", |rt, args, _| {
        let n = args[0].as_int().unwrap();
        if n == 0 {
            return Ok(int(0));
        }
        let below = rt.call("step", vec![int(n - 1)], vec![])?;
        Ok(int(below.as_int().unwrap() + 1))
    })
    .unwrap();
    rt.exec("def step(n):\n    return down(n)").unwrap();
    assert_eq!(rt.eval("add(40, 2)").unwrap(), int(42));
    assert_eq!(rt.eval("down(10)").unwrap(), int(10));
    assert_eq!(rt.eval("add('a')").unwrap_err().to_string(), "TypeError: add(a, b)");
    rt.define("named", |_, _, kwargs| Ok(Value::Str(kwargs[0].0.clone()))).unwrap();
    assert_eq!(rt.eval("named(key=1)").unwrap(), Value::from("key"));
    rt.define("nested_eval", |rt, _, _| rt.eval("1")).unwrap();
    assert_eq!(rt.eval("nested_eval()").unwrap_err().type_name(), Some("ValueError"));
}

#[test]
fn host_errors_come_back_as_their_cause() {
    let mut rt = Runtime::new().unwrap();
    rt.define("fail", |_, _, _| Err(Error::host(std::io::Error::other("disk on fire")))).unwrap();
    let Error::Python(e) = rt.eval("fail()").unwrap_err() else { panic!() };
    assert_eq!(e.type_name, "RuntimeError");
    assert_eq!(e.cause.unwrap().to_string(), "disk on fire");
    rt.exec("try:\n    fail()\nexcept RuntimeError as e:\n    caught = str(e)").unwrap();
    assert_eq!(rt.get("caught").unwrap(), Some("disk on fire".into()));
    // An engine exception passing through a host function keeps its identity.
    rt.define("relay", |rt, _, _| rt.call("boom", vec![], vec![])).unwrap();
    rt.exec("class Boom(Exception): pass\ndef boom(): raise Boom(7)").unwrap();
    rt.exec("try:\n    relay()\nexcept Boom as e:\n    got = e.args").unwrap();
    assert_eq!(rt.get("got").unwrap(), Some(Value::Tuple(vec![int(7)])));
}

#[test]
fn objects() {
    let mut rt = Runtime::new().unwrap();
    let Value::Object(d) = rt.eval("type('D', (dict,), {})(a=1)").unwrap() else { panic!() };
    assert_eq!(rt.get_item(&d, "a").unwrap(), int(1));
    rt.set_item(&d, "b", 2).unwrap();
    assert_eq!(rt.len(&d).unwrap(), 2);
    assert!(rt.contains(&d, "b").unwrap());
    assert!(rt.truth(&d).unwrap());
    assert_eq!(rt.get_item(&d, "zz").unwrap_err().type_name(), Some("KeyError"));
    assert_eq!(rt.repr(&d).unwrap(), "{'a': 1, 'b': 2}");
    rt.setattr(&d, "note", "hi").unwrap();
    assert_eq!(rt.getattr(&d, "note").unwrap(), Value::from("hi"));
    assert_eq!(rt.compare(&d, Compare::Eq, Value::Dict(vec![])).unwrap(), Value::Bool(false));
    let Value::Object(it) = rt.iter(&d).unwrap() else { panic!() };
    assert_eq!(rt.next(&it).unwrap(), Some("a".into()));
    assert_eq!(rt.next(&it).unwrap(), Some("b".into()));
    assert_eq!(rt.next(&it).unwrap(), None);
    let Value::Object(f) = rt.eval("lambda x, *, y=0: x + y").unwrap() else { panic!() };
    assert_eq!(rt.call(&f, vec![int(1)], vec![("y".into(), int(2))]).unwrap(), int(3));
    let mut other = Runtime::new().unwrap();
    assert!(matches!(other.set("x", &f), Err(Error::Invalid(_))));
}

#[test]
fn released_handles_are_freed() {
    let mut rt = Runtime::new().unwrap();
    rt.exec("import gc, weakref\nclass Box: pass\nrefs = []").unwrap();
    for _ in 0..100 {
        let object = rt.eval("b = Box(); refs.append(weakref.ref(b)); del b; refs[-1]()").unwrap();
        drop(object);
    }
    rt.collect().unwrap();
    assert_eq!(rt.eval("sum(r() is not None for r in refs)").unwrap(), int(0));
}

#[test]
fn output_and_loader() {
    let printed = Arc::new(Mutex::new(String::new()));
    let sink = printed.clone();
    let mut rt = Runtime::builder()
        .output(move |text| sink.lock().unwrap().push_str(text))
        .loader(|name| (name == "hello").then(|| "WORD = 'hi'".to_owned()))
        .spawn()
        .unwrap();
    rt.register_module("native", vec![("answer".into(), int(42))], "double = answer * 2").unwrap();
    rt.exec("import hello, native\nprint(hello.WORD, native.double)").unwrap();
    assert_eq!(*printed.lock().unwrap(), "hi 84\n");
}

#[test]
fn limits() {
    let mut rt = Runtime::builder().step_limit(10_000).memory_limit(16 << 20).spawn().unwrap();
    assert_eq!(rt.exec("while True: pass").unwrap_err().type_name(), Some("RuntimeError"));
    assert_eq!(rt.exec("x = 'a' * (64 << 20)").unwrap_err().type_name(), Some("MemoryError"));
    assert_eq!(rt.eval("1 + 1").unwrap(), int(2));
}

#[test]
fn timeout_ends_the_worker_but_not_while_the_host_runs() {
    let mut rt = Runtime::builder().timeout(Duration::from_millis(300)).spawn().unwrap();
    rt.define("slow", |_, _, _| {
        std::thread::sleep(Duration::from_millis(500));
        Ok(Value::None)
    })
    .unwrap();
    rt.eval("slow()").unwrap();
    let started = Instant::now();
    assert!(matches!(rt.exec("while True: pass"), Err(Error::Timeout(_))));
    assert!(started.elapsed() < Duration::from_secs(5));
    assert!(rt.is_closed());
    assert!(matches!(rt.eval("1"), Err(Error::Timeout(_))));
}

#[cfg(unix)]
#[test]
fn a_crashed_worker_is_lost() {
    for signal in ["SEGV", "ABRT", "KILL"] {
        let mut rt = Runtime::new().unwrap();
        let pid = rt.id().to_string();
        rt.define("crash", move |_, _, _| {
            std::process::Command::new("kill").arg(format!("-{signal}")).arg(&pid).status().unwrap();
            Ok(Value::None)
        })
        .unwrap();
        let error = rt.eval("crash() or [0 for _ in range(10**9)]").unwrap_err();
        let Error::Worker { message, status } = error else { panic!("{error:?}") };
        assert!(status.unwrap() < 0, "{message}");
        assert!(rt.eval("1").unwrap_err().is_lost());
    }
}

#[test]
fn a_panicking_host_function_loses_the_worker() {
    let mut rt = Runtime::new().unwrap();
    rt.define("boom", |_, _, _| panic!("boom")).unwrap();
    let unwound = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| rt.eval("boom()")));
    assert!(unwound.is_err());
    assert!(rt.eval("1").unwrap_err().is_lost());
}

#[test]
fn close_is_graceful() {
    let rt = Runtime::new().unwrap();
    rt.close();
}

#[cfg(target_os = "macos")]
#[test]
fn the_worker_is_sandboxed_once_code_runs() {
    let dir = std::env::temp_dir();
    let mut rt = Runtime::new().unwrap();
    rt.mount(&dir, Some("/data"), true).unwrap();
    rt.eval("1").unwrap();
    assert!(rt.mount(&dir, Some("/more"), true).unwrap_err().type_name() == Some("PermissionError"));
}
