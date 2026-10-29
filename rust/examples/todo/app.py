"""The todo application's rules, run by Small Python inside the Rust server.

Rust owns HTTP and JSON; this module owns the todos. Each function takes and
returns plain data, which crosses as JSON. ValueError is a bad request and
KeyError a missing todo. now() is a host function written in Rust.
"""

todos = []
next_id = 1


def _title(title):
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must be a non-empty string")
    if len(title) > 200:
        raise ValueError("title must be at most 200 characters")
    return title.strip()


def _find(id):
    for todo in todos:
        if todo["id"] == id:
            return todo
    raise KeyError(id)


def list_todos(show="all"):
    if show == "all":
        return todos
    if show not in ("active", "done"):
        raise ValueError(f"show must be all, active, or done, not {show!r}")
    return [todo for todo in todos if todo["done"] == (show == "done")]


def add(data):
    global next_id
    if not isinstance(data, dict):
        raise ValueError("expected an object")
    todo = {"id": next_id, "title": _title(data.get("title")), "done": False, "created": now()}
    next_id += 1
    todos.append(todo)
    return todo


def update(id, data):
    todo = _find(id)
    if not isinstance(data, dict):
        raise ValueError("expected an object")
    changes = {}
    for key, value in data.items():
        if key == "title":
            changes["title"] = _title(value)
        elif key == "done" and isinstance(value, bool):
            changes["done"] = value
        elif key == "done":
            raise ValueError("done must be true or false")
        else:
            raise ValueError(f"unknown field {key!r}")
    todo.update(changes)
    return todo


def remove(id):
    todos.remove(_find(id))


def stats():
    done = sum(1 for todo in todos if todo["done"])
    return {"total": len(todos), "done": done, "active": len(todos) - done}
