from enum import Enum, unique


class FieldParseError(Exception):
    @unique
    class Kind(Enum):
        noRequiredField = "required field is not present"
        wrongFieldType = "wrong field type"
        wrongEnumValue = "wrong enum value"

    __slots__ = ['kind', 'field_name', 'details']

    def __init__(self, kind: Kind, field_name: str, details=None):
        self.kind = kind
        self.field_name = field_name
        self.details = details

    def __str__(self):
        msg = f"Unable to parse field `{self.field_name}`: {self.kind.value}"
        if self.details is not None:
            msg = msg + f" ({self.details})"
        return msg

