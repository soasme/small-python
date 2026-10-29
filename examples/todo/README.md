# Todo

A todo web application: [axum](https://github.com/tokio-rs/axum) and tokio
serve HTTP and JSON, and the rules (validating titles, updating, filtering,
and counting todos) live in [`app.py`](app.py), which the
[`small-python`](../../rust/small-python) crate runs inside the server.
`ValueError` from Python is a 400 response, `KeyError` a 404.

```sh
cargo run          # then open http://127.0.0.1:3000; set ADDRESS to change it
cargo test
curl -d '{"title":"write docs"}' -H 'content-type: application/json' localhost:3000/todos
```
