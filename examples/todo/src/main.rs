//! A host that serves a Flask-style Python application with axum.
//!
//! Rust supplies what Python lacks here: the server and its routing (axum,
//! tokio) and JSON (serde_json, as the module `json`). `web.py`, built into
//! the host, turns them into a Flask-like `App`; the application is
//! `app.py` in the application directory, read at startup.
//!
//! ```sh
//! cargo run                   # then open http://127.0.0.1:3000
//! APP_DIR=path/to/app ADDRESS=0.0.0.0:8000 cargo run
//! ```

use std::collections::{BTreeMap, HashMap};
use std::path::Path;
use std::sync::{Arc, Mutex};

use axum::extract::{Query, RawPathParams, State};
use axum::http::{header, Method, StatusCode, Uri};
use axum::response::{IntoResponse, Response};
use axum::routing::{MethodFilter, MethodRouter};
use axum::{Json, Router};
use serde_json::json;
use small_python::{Error, Result, Runtime, Value};

/// One runtime holds the application and serves every request in turn.
struct Host {
    rt: Mutex<Runtime>,
}

impl Host {
    /// Runs `app.py` from `dir`, which `open()` sees read-only as the working
    /// directory; returns the host and the (method, path) of each route.
    fn load(dir: &Path) -> Result<(Host, Vec<(String, String)>)> {
        let rt = Runtime::new()?;
        rt.register_module("json", |rt, module| {
            module.setattr(
                "loads",
                rt.function("loads", |rt, args| {
                    let (text,): (String,) = args.extract()?;
                    let data: serde_json::Value =
                        serde_json::from_str(&text).map_err(|e| Error::new("ValueError", e.to_string()))?;
                    rt.to_value(&data)
                })?,
            )?;
            module.setattr(
                "dumps",
                rt.function("dumps", |rt, args| {
                    let (data,): (Value,) = args.extract()?;
                    rt.to_py(rt.from_value::<serde_json::Value>(&data)?.to_string())
                })?,
            )
        })?;
        rt.register_module("web", |rt, module| rt.exec_module(module, include_str!("../web.py"), "web.py"))?;
        rt.mount(dir, Some("/app"), true)?;
        let source = std::fs::read_to_string(dir.join("app.py"))
            .map_err(|e| Error::new("OSError", format!("cannot read app.py: {e}")))?;
        rt.exec(&source)?;
        let routes: Vec<(String, String, Value)> = rt.eval("__import__('web').routes")?;
        let routes = routes.into_iter().map(|(method, path, _)| (method, path)).collect();
        Ok((Host { rt: Mutex::new(rt) }, routes))
    }

    /// Runs route `index` through `web.dispatch`.
    fn handle(
        &self,
        index: usize,
        path: &str,
        params: HashMap<String, String>,
        args: HashMap<String, String>,
        body: String,
    ) -> Response {
        let rt = self.rt.lock().unwrap_or_else(|e| e.into_inner());
        let response = rt
            .eval::<Value>("__import__('web').dispatch")
            .and_then(|dispatch| dispatch.call::<(u16, String, String)>((index, path, params, args, body)));
        match response {
            Ok((status, content_type, text)) => {
                let status = StatusCode::from_u16(status).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR);
                (status, [(header::CONTENT_TYPE, content_type)], text).into_response()
            }
            Err(error) => {
                (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({ "error": error.to_string() }))).into_response()
            }
        }
    }
}

/// An axum route for each route `web.py` registered, by its position.
fn router(host: Arc<Host>, routes: Vec<(String, String)>) -> Router {
    let mut paths: BTreeMap<String, MethodRouter<Arc<Host>>> = BTreeMap::new();
    for (index, (method, path)) in routes.into_iter().enumerate() {
        let filter = Method::from_bytes(method.as_bytes())
            .ok()
            .and_then(|m| MethodFilter::try_from(m).ok())
            .unwrap_or_else(|| panic!("app.py routes the unsupported method {method}"));
        let handler = move |State(host): State<Arc<Host>>,
                            uri: Uri,
                            params: RawPathParams,
                            Query(args): Query<HashMap<String, String>>,
                            body: String| async move {
            let params = params.iter().map(|(k, v)| (k.to_owned(), v.to_owned())).collect();
            host.handle(index, uri.path(), params, args, body)
        };
        let methods = paths.remove(&path).unwrap_or_default();
        paths.insert(path, methods.on(filter, handler));
    }
    paths.into_iter().fold(Router::new(), |router, (path, methods)| router.route(&path, methods)).with_state(host)
}

#[tokio::main]
async fn main() {
    let dir = std::env::var("APP_DIR").unwrap_or_else(|_| env!("CARGO_MANIFEST_DIR").into());
    let (host, routes) = Host::load(Path::new(&dir)).unwrap_or_else(|e| panic!("{dir}/app.py: {e}"));
    let address = std::env::var("ADDRESS").unwrap_or_else(|_| "127.0.0.1:3000".into());
    let listener = tokio::net::TcpListener::bind(&address).await.expect("bind");
    println!("todo: serving {dir}/app.py on http://{address}");
    axum::serve(listener, router(Arc::new(host), routes)).await.expect("serve");
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::body::Body;
    use axum::http::Request;
    use http_body_util::BodyExt;
    use serde_json::Value as JsonValue;
    use tower::ServiceExt;

    fn app() -> Router {
        let (host, routes) = Host::load(Path::new(env!("CARGO_MANIFEST_DIR"))).unwrap();
        router(Arc::new(host), routes)
    }

    async fn send(router: &Router, method: &str, uri: &str, body: Option<JsonValue>) -> (StatusCode, JsonValue) {
        let request = Request::builder().method(method).uri(uri).header("content-type", "application/json");
        let body = body.map_or_else(Body::empty, |b| Body::from(b.to_string()));
        let response = router.clone().oneshot(request.body(body).unwrap()).await.unwrap();
        let status = response.status();
        let bytes = response.into_body().collect().await.unwrap().to_bytes();
        (status, serde_json::from_slice(&bytes).unwrap_or(JsonValue::Null))
    }

    #[tokio::test]
    async fn todos_round_trip() {
        let router = app();
        let (status, todo) = send(&router, "POST", "/todos", Some(json!({"title": "  write docs "}))).await;
        assert_eq!((status, todo), (StatusCode::CREATED, json!({"id": 1, "title": "write docs", "done": false})));
        send(&router, "POST", "/todos", Some(json!({"title": "ship"}))).await;

        let (status, todo) = send(&router, "PATCH", "/todos/1", Some(json!({"done": true}))).await;
        assert_eq!((status, todo["done"].clone()), (StatusCode::OK, json!(true)));
        let (_, done) = send(&router, "GET", "/todos?show=done", None).await;
        assert_eq!(done.as_array().unwrap().len(), 1);
        let (_, stats) = send(&router, "GET", "/stats", None).await;
        assert_eq!(stats, json!({"total": 2, "done": 1, "active": 1}));

        let (status, _) = send(&router, "DELETE", "/todos/1", None).await;
        assert_eq!(status, StatusCode::NO_CONTENT);
        let (_, all) = send(&router, "GET", "/todos", None).await;
        assert_eq!(all, json!([{"id": 2, "title": "ship", "done": false}]));
    }

    #[tokio::test]
    async fn aborts_are_http_errors() {
        let router = app();
        let (status, error) = send(&router, "POST", "/todos", Some(json!({"title": ""}))).await;
        assert_eq!((status, error), (StatusCode::BAD_REQUEST, json!({"error": "title must be a non-empty string"})));
        let (status, _) = send(&router, "PATCH", "/todos/9", Some(json!({"done": true}))).await;
        assert_eq!(status, StatusCode::NOT_FOUND);
        let (status, _) = send(&router, "GET", "/todos?show=maybe", None).await;
        assert_eq!(status, StatusCode::BAD_REQUEST);
        let request = Request::post("/todos").body(Body::from("not json")).unwrap();
        assert_eq!(router.clone().oneshot(request).await.unwrap().status(), StatusCode::BAD_REQUEST);
        let (status, _) = send(&router, "PUT", "/todos", None).await;
        assert_eq!(status, StatusCode::METHOD_NOT_ALLOWED);
    }

    #[tokio::test]
    async fn the_page_is_read_through_the_mount() {
        let response = app().oneshot(Request::get("/").body(Body::empty()).unwrap()).await.unwrap();
        assert_eq!(response.headers()[header::CONTENT_TYPE], "text/html; charset=utf-8");
        let page = response.into_body().collect().await.unwrap().to_bytes();
        assert!(String::from_utf8_lossy(&page).contains("<h1>Todos</h1>"));
    }
}
