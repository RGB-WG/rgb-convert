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
from openseals.data_types import OutPoint
from openseals.schema.schema import Schema
from openseals.schema.errors import SchemaError


class Seal(ImmutableSerializable):
    FIELDS = {
        'type': FieldParser(str),
        'outpoint': FieldParser(OutPoint),
    }

    __slots__ = list(FIELDS.keys()) + ['unparsed_state', 'seal_type', 'state']

    def __init__(self, schema_obj=None, **kwargs):
        for field_name, field in Seal.FIELDS.items():
            field.parse(self, kwargs, field_name)
        data = {}
        for item in kwargs.keys():
            if item not in Seal.FIELDS.keys():
                data[item] = kwargs[item]
        object.__setattr__(self, 'unparsed_state', data)
        object.__setattr__(self, 'state', None)
        object.__setattr__(self, 'seal_type', None)
        if isinstance(schema_obj, Schema):
            self.resolve_schema(schema_obj)

    def resolve_schema(self, schema: Schema):
        self.resolve_ref(schema.seal_types)
        if self.seal_type is not None:
            state = self.seal_type.state_from_dict(self.unparsed_state)
            object.__setattr__(self, 'state', state)

    def resolve_ref(self, seal_types: list):
        try:
            pos = next(num for num, type in enumerate(seal_types) if type.name == self.type)
            object.__setattr__(self, 'seal_type', seal_types[pos])
        except StopIteration:
            object.__setattr__(self, 'seal_type', None)

    @classmethod
    def stream_deserialize(cls, f, **kwargs):
        schema_obj = kwargs['schema_obj'] if 'schema_obj' not in kwargs else None
        if not isinstance(schema_obj, Schema):
            raise ValueError(f'`schema_obj` parameter must be of Schema type; got `{schema_obj}` instead')

        outpoint = OutPoint.stream_deserialize(f, short=True)

    def stream_serialize(self, f, **kwargs):
        state = kwargs['state'] if 'state' in kwargs else False
        if state is True:
            if self.seal_type is None:
                raise SchemaError(
                    f'Unable to serialize sealed state `{self.type}`: no schema seal type is provided for the value `{self.unparsed_state}`')
            self.seal_type.stream_serialize_state(self.state, f)
        else:
            self.outpoint.stream_serialize(f, short=True)
