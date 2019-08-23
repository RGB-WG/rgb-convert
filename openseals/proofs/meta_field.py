from bitcoin.core import ImmutableSerializable

from openseals.parser import *
from openseals.schema.schema import Schema


class MetaField(ImmutableSerializable):
    FIELDS = {
        'type': FieldParser(str, required=True),
    }

    __slots__ = list(FIELDS.keys()) + ['value', 'field_type']

    def __init__(self, name: str, value=None, schema_obj=None):
        for field_name, field in MetaField.FIELDS.items():
            field.parse(self, {'type': name}, field_name)
        object.__setattr__(self, 'value', value)
        if isinstance(schema_obj, Schema):
            self.resolve_ref(schema_obj.field_types)

    def resolve_ref(self, field_types: list):
        try:
            pos = next(num for num, type in enumerate(field_types) if type.name == self.type)
            object.__setattr__(self, 'field_type', field_types[pos])
        except StopIteration:
            object.__setattr__(self, 'field_type', None)


    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        pass

