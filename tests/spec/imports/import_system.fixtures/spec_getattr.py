def __getattr__(name):
    if name == "dynamic":
        return 42
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
def __dir__():
    return ["dynamic", "listed"]
