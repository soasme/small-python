# build: -c -N game level.py
# bundles: host_entries.py level.py shared.py
# description: -c writes several entries and one loader for a host; a module both import is embedded once and runs once in each context.
import shared
shared.log.append("menu")
assert shared.log == ["shared", "menu"]
