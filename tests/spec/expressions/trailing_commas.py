# spec: PLS-315 13.15
# description: Trailing commas in displays, calls, and definitions.
from harness import *
list1 = ["a", "b",]
list2 = [
    "a",
    "b",
]
assert list1 == list2

dict1 = {"a": "b",}
dict2 = {
    "a": "b",
}
#assert dict1 == dict2
