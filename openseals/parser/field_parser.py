import logging
from enum import IntEnum

from .errors import *


class FieldEnum(IntEnum):
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

        parsed = None
        try:
            val = kwargs[field_name]
        except KeyError:
            if self.required:
                raise FieldParseError(FieldParseError.Kind.noRequiredField, field_name)
        else:
            if self.recursive:
                logging.debug(f'--- recursively going through `{field_name}`')
                if self.array:
                    logging.debug('--- reading array')
                    if isinstance(val, list):
                        parsed = [self.field_type(**item) for item in val]
                    elif isinstance(val, dict):
                        parsed = []
                        for name, data in val.items():
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
            elif self.field_type(val) is not None:
                parsed = self.field_type(val)
            else:
                raise FieldParseError(FieldParseError.Kind.wrongFieldType, field_name)

        object.__setattr__(obj, field_name, parsed)
        return True if parsed is not None else False
