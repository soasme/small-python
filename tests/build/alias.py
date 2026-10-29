# build: --alias settings=settings_release
# bundles: alias.py settings_release.py
# oracle: skip
# description: --alias loads another module's file under the imported name.
import settings
assert settings.MODE == "release" and settings.__name__ == "settings"
