"""A Flask-style surface over the Rust host, which serves the routes
registered here with axum and supplies the json module from serde_json.

    from web import App, abort, request

    app = App()

    @app.get("/hello/{name}")
    def hello(name):
        return {"hello": name, "loud": request.args.get("loud") == "1"}

A view returns a str (HTML), anything json.dumps accepts, None (204), or a
(body, status) pair. Path parameters use axum's {name} syntax and arrive as
str keyword arguments.
"""
import json

routes = []  # (method, path, view): the host routes each method and path to its index


class HTTPError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def abort(status, message=""):
    raise HTTPError(status, message)


class Request:
    """The request being handled; the host serves one at a time."""

    @property
    def json(self):
        try:
            return json.loads(self.data)
        except ValueError:
            abort(400, "the body is not JSON")


request = Request()


class App:
    def route(self, path, methods=("GET",)):
        def register(view):
            for method in methods:
                routes.append((method, path, view))
            return view
        return register

    def get(self, path):
        return self.route(path, ("GET",))

    def post(self, path):
        return self.route(path, ("POST",))

    def put(self, path):
        return self.route(path, ("PUT",))

    def patch(self, path):
        return self.route(path, ("PATCH",))

    def delete(self, path):
        return self.route(path, ("DELETE",))


def dispatch(index, path, params, args, data):
    """Called by the host: runs a view, returns (status, content type, text)."""
    method, _, view = routes[index]
    request.__dict__.update(method=method, path=path, view_args=params, args=args, data=data)
    status = 200
    try:
        result = view(**params)
    except HTTPError as e:
        result, status = {"error": str(e)}, e.status
    if isinstance(result, tuple):
        result, status = result
    if result is None:
        return (204 if status == 200 else status), "text/plain", ""
    if isinstance(result, str):
        return status, "text/html; charset=utf-8", result
    return status, "application/json", json.dumps(result)
