# spec: PLS-315 12.2
# description: Comments anywhere a line may end.
from harness import *

# Snippet to demo comment handling...


def foo():
    a = []

    # This empty comment below manifests a bug:
    #
    if len(a) > 2:
        a.append(2)
    return a
