use std::collections::HashMap;
use std::sync::{Arc, Mutex};

use small_python::{Error, Runtime, Value};

#[test]
fn evaluates_and_converts() {
    let rt = Runtime::new().unwrap();
    assert_eq!(rt.eval::<i64>("6 * 7").unwrap(), 42);
    assert_eq!(rt.eval::<f64>("1 / 4").unwrap(), 0.25);
    assert_eq!(rt.eval::<String>("'spy' * 2").unwrap(), "spyspy");
    assert_eq!(rt.eval::<Vec<i64>>("[1, 2, 3]").unwrap(), [1, 2, 3]);
    assert_eq!(rt.eval::<(i64, String)>("(1, 'a')").unwrap(), (1, "a".to_owned()));
    assert_eq!(rt.eval::<Option<i64>>("None").unwrap(), None);
    let map: HashMap<String, i64> = rt.eval("{'a': 1, 'b': 2}").unwrap();
    assert_eq!(map, HashMap::from([("a".into(), 1), ("b".into(), 2)]));
    assert!(rt.eval::<bool>("1 < 2").unwrap());
}

#[test]
fn reports_exceptions() {
    let rt = Runtime::new().unwrap();
    let error = rt.exec("x = 1\nraise ValueError('bad')").unwrap_err();
    assert_eq!(error.type_name, "ValueError");
    assert_eq!(error.message, "bad");
    assert_eq!(error.line, Some(2));
    assert_eq!(error.to_string(), "ValueError: bad");
    assert_eq!(rt.eval::<i64>("x").unwrap(), 1, "the error is cleared and globals kept");
    assert_eq!(rt.eval::<i64>("'a'").unwrap_err().type_name, "TypeError");
    assert_eq!(rt.eval::<i8>("1000").unwrap_err().type_name, "OverflowError");
    assert_eq!(rt.eval::<i64>("1 +").unwrap_err().type_name, "SyntaxError");
    assert_eq!(rt.exec("a\0").unwrap_err().type_name, "SyntaxError");
}

#[test]
fn globals_round_trip() {
    let rt = Runtime::new().unwrap();
    rt.set("items", vec!["a", "b"]).unwrap();
    rt.set("pair", (1, 2.5)).unwrap();
    assert_eq!(rt.eval::<String>("'-'.join(items)").unwrap(), "a-b");
    assert_eq!(rt.eval::<f64>("pair[0] + pair[1]").unwrap(), 3.5);
    let items: Value = rt.get("items").unwrap();
    items.getattr("append").unwrap().call::<()>(("c",)).unwrap();
    assert_eq!(rt.get::<Vec<String>>("items").unwrap(), ["a", "b", "c"]);
}

#[test]
fn host_functions() {
    let rt = Runtime::new().unwrap();
    rt.define("add", |rt, args| {
        let (a, b): (i64, i64) = args.extract()?;
        rt.to_py(a + b)
    })
    .unwrap();
    rt.define("greet", |rt, args| {
        let (name,): (String,) = args.extract()?;
        let punctuation: String = match args.keyword("end")? {
            Some(end) => end.extract()?,
            None => "!".into(),
        };
        rt.to_py(format!("hello {name}{punctuation}"))
    })
    .unwrap();
    rt.define("apply", |_, args| {
        let (f, x): (Value, Value) = args.extract()?;
        f.call((x,))
    })
    .unwrap();
    assert_eq!(rt.eval::<i64>("add(40, 2)").unwrap(), 42);
    assert_eq!(rt.eval::<String>("greet('spy')").unwrap(), "hello spy!");
    assert_eq!(rt.eval::<String>("greet('spy', end='?')").unwrap(), "hello spy?");
    assert_eq!(rt.eval::<i64>("apply(lambda n: n * 2, 21)").unwrap(), 42);
    let error = rt.eval::<i64>("add(1)").unwrap_err();
    assert_eq!((error.type_name.as_str(), error.message.as_str()), ("TypeError", "expected 2 arguments, got 1"));
    rt.exec("try:\n    add('a', 1)\nexcept TypeError as e:\n    caught = 'yes'").unwrap();
    assert_eq!(rt.get::<String>("caught").unwrap(), "yes");
}

#[test]
fn host_errors_and_panics_become_exceptions() {
    let rt = Runtime::new().unwrap();
    rt.define("fail", |_, _| Err(Error::new("KeyError", "missing"))).unwrap();
    rt.define("boom", |_, _| panic!("boom")).unwrap();
    rt.exec("try:\n    fail()\nexcept KeyError:\n    ok = True").unwrap();
    assert!(rt.get::<bool>("ok").unwrap());
    let error = rt.eval::<()>("boom()").unwrap_err();
    assert_eq!(error.type_name, "RuntimeError");
    assert_eq!(rt.eval::<i64>("1").unwrap(), 1);
}

#[test]
fn output_loader_and_modules() {
    let rt = Runtime::new().unwrap();
    let printed = Arc::new(Mutex::new(String::new()));
    let sink = printed.clone();
    rt.set_output(move |text| sink.lock().unwrap().push_str(text));
    rt.set_loader(|name| (name == "greeting").then(|| "WORD = 'hi'\n".to_owned()));
    rt.register_module("native", |rt, module| {
        module.setattr("answer", 42)?;
        rt.exec_module(module, "double = answer * 2", "<native>")
    })
    .unwrap();
    rt.exec("import greeting, native\nprint(greeting.WORD, native.double)").unwrap();
    assert_eq!(*printed.lock().unwrap(), "hi 84\n");
    assert_eq!(rt.exec("import nothing").unwrap_err().type_name, "ModuleNotFoundError");
}

#[test]
fn std_modules_are_optional() {
    assert!(Runtime::new().unwrap().exec("import sys").is_ok());
    assert!(Runtime::bare().unwrap().exec("import sys").is_err());
}

#[test]
fn step_limit() {
    let rt = Runtime::new().unwrap();
    rt.set_step_limit(10_000);
    assert_eq!(rt.exec("while True: pass").unwrap_err().type_name, "RuntimeError");
    assert_eq!(rt.eval::<i64>("1 + 1").unwrap(), 2);
}

#[test]
fn iteration_and_items() {
    let rt = Runtime::new().unwrap();
    let squares: Value = rt.eval("(n * n for n in range(4))").unwrap();
    let got: Vec<i64> = squares.iter().unwrap().map(|v| v.unwrap().extract().unwrap()).collect();
    assert_eq!(got, [0, 1, 4, 9]);
    let d: Value = rt.eval("{}").unwrap();
    d.set_item("k", vec![1, 2]).unwrap();
    assert_eq!(d.get_item("k").unwrap().repr().unwrap(), "[1, 2]");
    assert_eq!(d.get_item("x").unwrap_err().type_name, "KeyError");
    assert_eq!(format!("{d:?}"), "{'k': [1, 2]}");
    let failing: Value = rt.eval("(1 // 0 for _ in range(1))").unwrap();
    assert_eq!(failing.iter().unwrap().next().unwrap().unwrap_err().type_name, "ZeroDivisionError");
}

#[test]
fn values_of_another_runtime_are_refused() {
    let a = Runtime::new().unwrap();
    let b = Runtime::new().unwrap();
    let v: Value = a.eval("[]").unwrap();
    assert_eq!(b.set("x", &v).unwrap_err().type_name, "ValueError");
}

#[test]
fn runtime_moves_between_threads() {
    let rt = Runtime::new().unwrap();
    rt.exec("n = 1").unwrap();
    let rt = std::thread::spawn(move || {
        rt.exec("n += 1").unwrap();
        rt
    })
    .join()
    .unwrap();
    assert_eq!(rt.get::<i64>("n").unwrap(), 2);
}

#[cfg(feature = "serde")]
#[test]
fn serde_round_trip() {
    use serde::{Deserialize, Serialize};

    #[derive(Serialize, Deserialize, Debug, PartialEq)]
    enum Shape {
        Point,
        Circle(f64),
        Rect { w: f64, h: f64 },
    }

    #[derive(Serialize, Deserialize, Debug, PartialEq)]
    struct Doc {
        title: String,
        tags: Vec<String>,
        done: bool,
        rank: Option<u32>,
        shapes: Vec<Shape>,
    }

    let rt = Runtime::new().unwrap();
    let doc = Doc {
        title: "t".into(),
        tags: vec!["a".into()],
        done: false,
        rank: None,
        shapes: vec![Shape::Point, Shape::Circle(1.5), Shape::Rect { w: 1.0, h: 2.0 }],
    };
    let value = rt.to_value(&doc).unwrap();
    assert_eq!(
        value.repr().unwrap(),
        "{'title': 't', 'tags': ['a'], 'done': False, 'rank': None, \
         'shapes': ['Point', {'Circle': 1.5}, {'Rect': {'w': 1.0, 'h': 2.0}}]}"
    );
    assert_eq!(rt.from_value::<Doc>(&value).unwrap(), doc);
    let error = rt.from_value::<Doc>(&rt.eval("{'title': 1}").unwrap()).unwrap_err();
    assert_eq!(error.type_name, "ValueError");
}
