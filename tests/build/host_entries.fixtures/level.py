import shared
shared.log.append("level")
assert shared.log == ["shared", "level"]
