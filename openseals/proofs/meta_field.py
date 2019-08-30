# This file is a part of Python OpenSeals library and tools
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

from bitcoin.core.serialize import ImmutableSerializable

from openseals.parser import *
from openseals.schema.schema import Schema
from openseals.schema.errors import SchemaError


class MetaField(ImmutableSerializable, StructureSerializable):
    FIELDS = {
        'type_name': FieldParser(str, required=True),
    }

    __slots__ = list(FIELDS.keys()) + ['value', 'str_value', 'field_type']

    def __init__(self, type_name: str, value=None, schema_obj=None):
        for field_name, field in MetaField.FIELDS.items():
            field.parse(self, {'type_name': type_name}, field_name)
        object.__setattr__(self, 'value', value)
        object.__setattr__(self, 'str_value', value)
        object.__setattr__(self, 'field_type', None)
        if isinstance(schema_obj, Schema):
            self.resolve_schema(schema_obj)

    def resolve_schema(self, schema: Schema):
        if not isinstance(schema, Schema):
            raise ValueError(f'`schema` parameter must be of Schema type; got `{schema}` instead')

        self.resolve_schema_refs(schema.field_types)
        if self.field_type is None:
            raise SchemaError(f'the provided schema `{schema.name}` does not define field type `{self.type_name}`')

        value = self.field_type.value_from_str(self.str_value)
        object.__setattr__(self, 'value', value)

    def resolve_schema_refs(self, field_types: list):
        try:
            pos = next(num for num, type in enumerate(field_types) if type.name == self.type_name)
            object.__setattr__(self, 'field_type', field_types[pos])
        except StopIteration:
            object.__setattr__(self, 'field_type', None)

    def parse_field(self, metadata: bytes, pos: int) -> int:
        if self.field_type is None:
            raise SchemaError("can't parse field value from metadata without knowing `field_type` of the field")
        value, shift = self.field_type.value_from_blob(metadata[pos:-1])
        object.__setattr__(self, 'value', value)
        return pos + shift

    def structure_serialize(self, **kwargs) -> dict:
        return {self.type_name: self.value}

    @classmethod
    def stream_deserialize(cls, f, **kwargs):
        raise NotImplementedError(
            "MetaField can't be directly deserealized; use FieldType coming with the schema instead")

    def stream_serialize(self, f, **kwargs):
        if self.field_type is None:
            raise SchemaError(
                f'Unable to serialize field `{self.type}`: no schema field type is provided for a value `{self.value}`')
        self.field_type.stream_serialize_value(self.value, f)
