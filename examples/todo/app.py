"""A todo list in the style of Flask, served by the Rust host with axum."""
from web import App, abort, request

app = App()
todos = []
next_id = 1


def title_of(data):
    title = data.get("title") if isinstance(data, dict) else None
    if not isinstance(title, str) or not title.strip():
        abort(400, "title must be a non-empty string")
    if len(title) > 200:
        abort(400, "title must be at most 200 characters")
    return title.strip()


def find(id):
    for todo in todos:
        if str(todo["id"]) == id:
            return todo
    abort(404, f"no todo {id}")


@app.get("/")
def index():
    with open("index.html") as page:
        return page.read()


@app.get("/todos")
def list_todos():
    show = request.args.get("show", "all")
    if show == "all":
        return todos
    if show not in ("active", "done"):
        abort(400, f"show must be all, active, or done, not {show!r}")
    return [todo for todo in todos if todo["done"] == (show == "done")]


@app.post("/todos")
def add():
    global next_id
    todo = {"id": next_id, "title": title_of(request.json), "done": False}
    next_id += 1
    todos.append(todo)
    return todo, 201


@app.patch("/todos/{id}")
def update(id):
    todo = find(id)
    data = request.json
    if not isinstance(data, dict):
        abort(400, "expected an object")
    changes = {}
    for key, value in data.items():
        if key == "title":
            changes["title"] = title_of(data)
        elif key == "done" and isinstance(value, bool):
            changes["done"] = value
        else:
            abort(400, f"invalid field {key!r}")
    todo.update(changes)
    return todo


@app.delete("/todos/{id}")
def remove(id):
    todos.remove(find(id))


@app.get("/stats")
def stats():
    done = sum(1 for todo in todos if todo["done"])
    return {"total": len(todos), "done": done, "active": len(todos) - done}
