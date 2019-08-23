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

import logging
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


class FieldEnum(Enum):
    @classmethod
    def from_str(cls, val: str):
        return cls.__members__[val]


class FieldParser:
    """Small automation class for checking fields coming from deserealized JSON, YAML etc"""

    __slots__ = ['field_type', 'required', 'recursive', 'array', 'enum']

    def __init__(self, field_type: type, required=True, recursive=False, array=False):
        self.field_type = field_type
        self.required = required
        self.recursive = recursive
        self.array = array
        if array and not recursive:
            raise FieldParseError(FieldParseError.Kind.nonRecursiveArray, self.field_type.__name__)

    def parse(self, obj: object, kwargs, field_name: str) -> bool:
        """Assigns a value of a proper type from the `kwargs` and returns whether the required field was presented"""
        logging.debug(f'-- parsing field `{field_name}` of `{self.field_type}`')

        try:
            val = kwargs[field_name]
        except KeyError:
            raise FieldParseError(FieldParseError.Kind.noRequiredField, field_name)

        parsed = None
        if self.recursive:
            logging.debug(f'--- recursively going through `{field_name}`')
            if self.array:
                if isinstance(val, list):
                    logging.debug('---- detected array')
                    parsed = [self.field_type(**item) for item in val]
                elif isinstance(val, dict):
                    logging.debug('---- detected dictionary')
                    parsed = []
                    for name, data in val.items():
                        logging.debug(f'---- element `{name}` with data `{data}`')
                        if isinstance(data, dict):
                            v = self.field_type(name, **data)
                        elif isinstance(data, list):
                            v = self.field_type(name, *data)
                        else:
                            v = self.field_type(name, data)
                        parsed.append(v)
                else:
                    raise FieldParseError(FieldParseError.Kind.wrongFieldType, field_name)
            else:
                parsed = self.field_type(**val)
        elif issubclass(self.field_type, FieldEnum) and isinstance(val, str):
            logging.debug('--- detected enum')
            try:
                parsed = self.field_type.from_str(val)
            except KeyError as err:
                raise FieldParseError(FieldParseError.Kind.wrongEnumValue, field_name,
                                      f'`{val}` is not a member of enum `{self.field_type}`')
        elif isinstance(val, self.field_type):
            parsed = val
        else:
            raise FieldParseError(FieldParseError.Kind.wrongFieldType, field_name)

        if parsed is not None:
            object.__setattr__(obj, field_name, parsed)
            return True
        return False
