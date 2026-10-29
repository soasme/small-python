//! A todo web application: axum serves HTTP and JSON, and the rules live in
//! app.py, which Small Python runs inside this process.
//!
//! ```sh
//! cargo run -p todo            # then open http://127.0.0.1:3000
//! curl -d '{"title":"write docs"}' -H 'content-type: application/json' localhost:3000/todos
//! ```

use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};

use axum::extract::{Path, Query, State};
use axum::http::StatusCode;
use axum::response::{Html, IntoResponse, Response};
use axum::routing::get;
use axum::{Json, Router};
use serde_json::{json, Value as JsonValue};
use small_python::{Runtime, Value};

/// One runtime holds the todos and serves every request in turn; each call
/// into it takes microseconds.
struct App {
    rt: Mutex<Runtime>,
}

impl App {
    fn new() -> small_python::Result<App> {
        let rt = Runtime::new()?;
        rt.define("now", |rt, _| {
            let seconds = SystemTime::now().duration_since(UNIX_EPOCH).map_or(0, |d| d.as_secs());
            rt.to_py(seconds)
        })?;
        rt.exec(include_str!("../app.py"))?;
        Ok(App { rt: Mutex::new(rt) })
    }

    /// Calls the app.py function `name` with JSON arguments.
    fn call(&self, name: &str, args: Vec<JsonValue>) -> Result<JsonValue, ApiError> {
        let rt = self.rt.lock().unwrap_or_else(|e| e.into_inner());
        let function: Value = rt.get(name)?;
        let args = args.iter().map(|arg| rt.to_value(arg)).collect::<Result<Vec<_>, _>>()?;
        let result: Value = function.call(args)?;
        Ok(rt.from_value(&result)?)
    }
}

/// A Python exception as an HTTP error.
struct ApiError(small_python::Error);

impl From<small_python::Error> for ApiError {
    fn from(error: small_python::Error) -> ApiError {
        ApiError(error)
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let status = match self.0.type_name.as_str() {
            "ValueError" => StatusCode::BAD_REQUEST,
            "KeyError" => StatusCode::NOT_FOUND,
            _ => StatusCode::INTERNAL_SERVER_ERROR,
        };
        (status, Json(json!({ "error": self.0.to_string() }))).into_response()
    }
}

type Shared = State<Arc<App>>;

async fn page() -> Html<&'static str> {
    Html(include_str!("../index.html"))
}

async fn list(State(app): Shared, Query(query): Query<JsonValue>) -> Result<Json<JsonValue>, ApiError> {
    let show = query.get("show").cloned().unwrap_or_else(|| "all".into());
    Ok(Json(app.call("list_todos", vec![show])?))
}

async fn add(State(app): Shared, Json(body): Json<JsonValue>) -> Result<(StatusCode, Json<JsonValue>), ApiError> {
    Ok((StatusCode::CREATED, Json(app.call("add", vec![body])?)))
}

async fn update(
    State(app): Shared,
    Path(id): Path<i64>,
    Json(body): Json<JsonValue>,
) -> Result<Json<JsonValue>, ApiError> {
    Ok(Json(app.call("update", vec![id.into(), body])?))
}

async fn remove(State(app): Shared, Path(id): Path<i64>) -> Result<StatusCode, ApiError> {
    app.call("remove", vec![id.into()])?;
    Ok(StatusCode::NO_CONTENT)
}

async fn stats(State(app): Shared) -> Result<Json<JsonValue>, ApiError> {
    Ok(Json(app.call("stats", vec![])?))
}

fn router(app: Arc<App>) -> Router {
    Router::new()
        .route("/", get(page))
        .route("/todos", get(list).post(add))
        .route("/todos/{id}", axum::routing::patch(update).delete(remove))
        .route("/stats", get(stats))
        .with_state(app)
}

#[tokio::main]
async fn main() {
    let app = Arc::new(App::new().expect("app.py loads"));
    let address = std::env::var("ADDRESS").unwrap_or_else(|_| "127.0.0.1:3000".into());
    let listener = tokio::net::TcpListener::bind(&address).await.expect("bind");
    println!("todo: listening on http://{address}");
    axum::serve(listener, router(app)).await.expect("serve");
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::body::Body;
    use axum::http::Request;
    use http_body_util::BodyExt;
    use tower::ServiceExt;

    async fn send(router: &Router, method: &str, uri: &str, body: Option<JsonValue>) -> (StatusCode, JsonValue) {
        let request = Request::builder().method(method).uri(uri).header("content-type", "application/json");
        let body = body.map_or_else(Body::empty, |b| Body::from(b.to_string()));
        let response = router.clone().oneshot(request.body(body).unwrap()).await.unwrap();
        let status = response.status();
        let bytes = response.into_body().collect().await.unwrap().to_bytes();
        (status, if bytes.is_empty() { JsonValue::Null } else { serde_json::from_slice(&bytes).unwrap() })
    }

    #[tokio::test]
    async fn todos_round_trip() {
        let router = router(Arc::new(App::new().unwrap()));
        let (status, todo) = send(&router, "POST", "/todos", Some(json!({"title": "  write docs "}))).await;
        assert_eq!(status, StatusCode::CREATED);
        assert_eq!(
            (todo["id"].clone(), todo["title"].clone(), todo["done"].clone()),
            (json!(1), json!("write docs"), json!(false))
        );
        assert!(todo["created"].as_u64().unwrap() > 1_700_000_000);
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
        assert_eq!(all[0]["title"], json!("ship"));
    }

    #[tokio::test]
    async fn python_exceptions_are_http_errors() {
        let router = router(Arc::new(App::new().unwrap()));
        let (status, error) = send(&router, "POST", "/todos", Some(json!({"title": ""}))).await;
        assert_eq!(
            (status, error["error"].clone()),
            (StatusCode::BAD_REQUEST, json!("ValueError: title must be a non-empty string"))
        );
        let (status, _) = send(&router, "PATCH", "/todos/9", Some(json!({"done": true}))).await;
        assert_eq!(status, StatusCode::NOT_FOUND);
        let (status, _) = send(&router, "GET", "/todos?show=maybe", None).await;
        assert_eq!(status, StatusCode::BAD_REQUEST);
        send(&router, "POST", "/todos", Some(json!({"title": "x"}))).await;
        let (status, error) = send(&router, "PATCH", "/todos/1", Some(json!({"owner": "me"}))).await;
        assert_eq!(
            (status, error["error"].clone()),
            (StatusCode::BAD_REQUEST, json!("ValueError: unknown field 'owner'"))
        );
    }
}
