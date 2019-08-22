# This file is a part of Python OpenSeals library
# Written in 2019 by
#     Dr. Maxim Orlovsky <orlovsky@pandoracore.com>, Pandora Core AG, Swiss
#     with support of Bitfinex and other RGB project contributors
#
# To the extent possible under law, the author(s) have dedicated all
# copyright and related and neighboring rights to this software to
# the public domain worldwide. This software is distributed without
# any warranty.
#
# You should have received a copy of the MIT License
# along with this software.
# If not, see <https://opensource.org/licenses/MIT>.

from enum import Enum, unique


class FieldParseError(Exception):
    @unique
    class Kind(Enum):
        noRequiredField = "required field is not present"
        wrongFieldType = "wrong field type"
        nonRecursiveArray = "arrays must be always recursive"
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
        return  msg


class FieldParser:
    """Small automation class for checking fields coming from deserealized JSON, YAML etc"""

    __slots__ = ['field_type', 'required', 'recursive', 'array']

    def __init__(self, field_type: type, required=True, recursive=False, array=False):
        self.field_type = field_type
        self.required = required
        self.recursive = recursive
        self.array = array
        if array and not recursive:
            raise FieldParseError(FieldParseError.Kind.nonRecursiveArray, self.field_type.__name__)

    def parse(self, obj: object, kwargs, field_name: str) -> bool:
        """Assigns a value of a proper type from the `kwargs` and returns whether the required field was presented"""
        val = kwargs[field_name]
        parsed = None
        if self.required and val is None:
            raise FieldParseError(FieldParseError.Kind.noRequiredField, field_name)
        if self.recursive:
            if self.array:
                if isinstance(val, list):
                    parsed = [self.field_type(**item) for item in val]
                else:
                    raise FieldParseError(FieldParseError.Kind.wrongFieldType, field_name)
            else:
                parsed = self.field_type(**val)
        elif isinstance(val, self.field_type):
            parsed = val
        else:
            raise FieldParseError(FieldParseError.Kind.wrongFieldType, field_name)
        if parsed is not None:
            object.__setattr__(obj, field_name, parsed)
            return True
        return False
