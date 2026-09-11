"""JSON numeric semantics approved for the FC specification audit."""


def is_integer(value: object) -> bool:
    """Accept integer-valued JSON numbers, excluding booleans and nonfinite floats."""
    return type(value) is int or (isinstance(value, float) and value.is_integer())
