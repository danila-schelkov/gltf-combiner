def pascal_case(value: str):
    """
    Converts glTF camel case variable names to Pascal Case like in Flatbuffer
    """
    return value[0].upper() + value[1:]
