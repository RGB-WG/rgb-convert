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
    def stream_deserialize(cls, f, **kwargs):
        if 'schema_obj' not in kwargs:
            raise AttributeError('MetaField.stream_deserialize must be provided with `schema_obj` parameter')
        schema_obj = kwargs['schema_obj']
        if not isinstance(schema_obj, Schema):
            raise ValueError(f'`schema_obj` parameter must be of Schema type; got `{schema_obj}` instead')

        self.field_type.stream_deserialize_value(f)

    def stream_serialize(self, f, **kwargs):
        if self.field_type is None:
            raise SchemaError(
                f'Unable to serialize field `{self.type}`: no schema field type is provided for a value `{self.value}`')
        self.field_type.stream_serialize_value(self.value, f)
