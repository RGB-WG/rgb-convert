from bitcoin.core import ImmutableSerializable

from openseals.parser import *
from openseals.schema.schema import Schema
from openseals.schema.errors import SchemaError


class MetaField(ImmutableSerializable):
    FIELDS = {
        'type': FieldParser(str, required=True),
    }

    __slots__ = list(FIELDS.keys()) + ['value', 'field_type']

    def __init__(self, name: str, value=None, schema_obj=None):
        for field_name, field in MetaField.FIELDS.items():
            field.parse(self, {'type': name}, field_name)
        object.__setattr__(self, 'value', value)
        object.__setattr__(self, 'field_type', None)
        if isinstance(schema_obj, Schema):
            self.resolve_schema(schema_obj)

    def resolve_schema(self, schema: Schema):
        self.resolve_ref(schema.field_types)
        if self.field_type is not None:
            value = self.field_type.value_from_str(self.value)
            object.__setattr__(self, 'value', value)

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
        if self.field_type is None:
            raise SchemaError(
                f'Unable to serialize field `{self.type}`: no schema field type is provided for the value `{self.value}`')
        self.field_type.stream_serialize_value(self.value, f)
