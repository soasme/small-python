"""Module for testing the behavior of generics across different modules."""

# (Ported) Only the two aliases test_type_aliases reads are kept; the generic
# classes need the typing module. TypeAliasType is the type of an alias.
type Alias = int
OldStyle = type(Alias)("OldStyle", int)
