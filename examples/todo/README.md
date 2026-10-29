# Todo

A todo list written like a Flask application, [`app.py`](app.py), served by
a small Rust host. The host knows nothing about todos: it supplies what
Small Python lacks, and the application does the rest. It uses the
[`small-python`](https://crates.io/crates/small-python) crate from
crates.io, as any program would.

| Layer | Supplies |
|---|---|
| Rust ([`src/main.rs`](src/main.rs)) | the server and routing (axum, tokio); a `json` module (`loads`, `dumps`) on serde_json; `app.py`'s directory mounted read-only for `open()` |
| [`web.py`](web.py), built into the host | `App` with `route`, `get`, `post`, `put`, `patch`, `delete`; `request` (`method`, `path`, `args`, `view_args`, `data`, `json`); `abort(status, message)` |
| [`app.py`](app.py) | the todos |

```python
from web import App, abort, request

app = App()

@app.patch("/todos/{id}")
def update(id):
    todo = find(id)          # abort(404, ...) when missing
    todo.update(request.json)
    return todo
```

A view returns a `str` (HTML), anything `json.dumps` accepts, `None` (204),
or a `(body, status)` pair. Paths use axum's `{name}` syntax; parameters
arrive as `str` keyword arguments. After running `app.py` the host reads
`web.routes` and gives each method and path an axum route that calls
`web.dispatch`. One runtime serves the requests in turn.

```sh
cargo run          # http://127.0.0.1:3000; APP_DIR and ADDRESS change the app and address
cargo test
curl -d '{"title":"write docs"}' localhost:3000/todos
```
