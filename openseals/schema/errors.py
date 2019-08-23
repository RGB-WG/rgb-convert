class SchemaError(Exception):
    pass


class SchemaInternalRefError(SchemaError):
    __slots__ = ['ref_type', 'ref_name', 'section']

    def __init__(self, ref_type: str, ref_name: str, section: str):
        self.ref_type = ref_type
        self.ref_name = ref_name
        self.section = section

    def __str__(self):
        return f'Unable to resolve {self.ref_type} reference inside `{self.section}` named `{self.ref_name}`'


class SchemaValidationError(SchemaError):
    __slots__ = ['description']

    def __init__(self, description: str):
        self.description = description

    def __str__(self):
        return self.description
