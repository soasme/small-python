"""The game apart from drawing: a bird, the pipes, and the world that runs
them. Nothing here imports raylib, so the rules run on plain spy too."""
from .bird import Bird
from .pipes import Pipes
from .world import World

# `from game import *` also brings the tuning submodule; spyc reads this
# literal list and bundles the modules it names.
__all__ = ["Bird", "Pipes", "World", "tuning"]
