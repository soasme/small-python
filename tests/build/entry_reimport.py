# build:
# bundles: entry_reimport.py log.py
# description: importing the entry by name runs a second module, apart from __main__.
import log
log.events.append(__name__)
if __name__ == "__main__":
    import entry_reimport
    assert log.events == ["__main__", "entry_reimport"]
    assert entry_reimport.__name__ == "entry_reimport"
