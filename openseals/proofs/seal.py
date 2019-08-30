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

from bitcoin.core.serialize import ImmutableSerializable, BytesSerializer

from openseals.consensus import SeparatorByteSignal
from openseals.parser import *
from openseals.data_types import OutPoint
from openseals.schema.schema import Schema
from openseals.schema.errors import SchemaError


class Seal(ImmutableSerializable):
    """Data structure representing single use seal and an associated state. The state can be represented in the
    following forms:
    * if the seal is read from the binary proof data, it does not hold any state data, but may acquire the state data
      later when it will be provided with a schema;
    * if the seal is created on the fly, then it may be provided with the blob state data;
    * if the seal is read from the structured data file (like YAML or JSON) it holds state as a dictionary data
      from the source in its `dict_state` field and human-readable name for the state type in the `type` field,
      which is used during schema association procedure (see below).

    In all cases, the seal can know the structure of the state through an associated schema. Seal gets schema
    either during construction (`schema_obj` parameter of constructor and `stream_deserealize` methods) or
    by calling `resolve_schema` method. Proof can be initialized/created without schema, however in this case
    it will be impossible to transcode the data from `state` to `dict_state` and vice-verse, i.e. proof
    can be serialized with consensus rules only if it was read from the binary proof, not from structured data source.
    """

    FIELDS = {
        'type_name': FieldParser(str),
        'outpoint': FieldParser(OutPoint),
    }

    __slots__ = list(FIELDS.keys()) + ['type_no', 'seal_type', 'state', 'dict_state']

    def __init__(self, outpoint, type_name=None, type_no=None, schema_obj=None, state=None, **kwargs):
        object.__setattr__(self, 'state', state)
        object.__setattr__(self, 'type_no', type_no)

        if isinstance(outpoint, OutPoint):
            # Reading from consensus-deserialized data or constructing from scratch
            object.__setattr__(self, 'type_name', type_name)
            object.__setattr__(self, 'outpoint', outpoint)
            object.__setattr__(self, 'dict_state', None)
        else:
            # Reading from structured data source
            for field_name, field in Seal.FIELDS.items():
                field.parse(self, {'type_name': type_name, 'outpoint': outpoint}, field_name)
            data = {}
            for item in kwargs.keys():
                if item not in Seal.FIELDS.keys():
                    data[item] = kwargs[item]
            object.__setattr__(self, 'dict_state', data)

        object.__setattr__(self, 'seal_type', None)
        if isinstance(schema_obj, Schema):
            self.resolve_schema(schema_obj)

    def resolve_schema(self, schema: Schema):
        if not isinstance(schema, Schema):
            raise ValueError(f'`schema` parameter must be of Schema type; got `{schema}` instead')

        self.resolve_schema_refs(schema.seal_types)
        if self.seal_type is None:
            raise SchemaError(f'the provided schema `{schema.name}` does not define seal type `{self.type_name}`'
                              f'or type with index number {self.type_no}')

        if self.dict_state is not None:
            state = self.seal_type.state_from_dict(self.dict_state)
            object.__setattr__(self, 'state', state)

    def resolve_schema_refs(self, seal_types: list):
        try:
            seal_type = seal_types[self.type_no]
            object.__setattr__(self, 'type_name', seal_type.name)
        except:
            try:
                pos = next(num for num, type in enumerate(seal_types) if type.name == self.type_name)
                seal_type = seal_types[pos]
                object.__setattr__(self, 'type_no', pos)
            except StopIteration:
                seal_type = None

        object.__setattr__(self, 'seal_type', seal_type)

    def parse_state_from_blob(self, state: bytes, pos: int) -> int:
        if self.seal_type is None:
            raise SchemaError("can't parse state data without knowing `seal_type` of the seal")
        state, shift = self.seal_type.state_from_blob(state[pos:])
        object.__setattr__(self, 'state', state)
        return pos + shift

    def structure_serialize(self, **kwargs) -> dict:
        if self.seal_type is None:
            raise SchemaError("can't serialize state data without knowing `seal_type` of the seal")
        data = self.seal_type.dict_from_state(self.state)
        for field_name in Seal.FIELDS.keys():
            value = self.__getattribute__(field_name)
            if issubclass(type(value), StructureSerializable) or issubclass(type(value), FieldEnum):
                value = value.structure_serialize(**kwargs)
            data[field_name] = value
        return data

    @classmethod
    def stream_deserialize(cls, f, **kwargs):
        if 'schema_obj' not in kwargs:
            raise AttributeError('Seal.stream_deserialize must be provided with `schema_obj` parameter')
        schema_obj = kwargs['schema_obj'] if 'schema_obj' in kwargs else None
        if not isinstance(schema_obj, Schema):
            raise ValueError(f'`schema_obj` parameter must be of Schema type; got `{schema_obj}` instead')

        type_no = kwargs['type_no'] if 'type_no' in kwargs else None
        if type_no is None:
            raise ValueError('seal deserialization requires `type_no` parameter, while no parameter was provided')

        outpoint = OutPoint.stream_deserialize(f, short=True)
        return Seal(outpoint=outpoint, type_no=type_no)

    def stream_serialize(self, f, **kwargs):
        state = kwargs['state'] if 'state' in kwargs else False
        if state is True:
            if self.seal_type is not None:
                self.seal_type.stream_serialize_state(self.state, f)
            elif self.state is not None:
                BytesSerializer.stream_serialize(self.state, f)
            else:
                raise SchemaError(
                    f'''Unable to consensus-serialize sealed state: no binary state and no schema seal type are 
                    provided for the value `{self.dict_state}`
                    ''')
        else:
            self.outpoint.stream_serialize(f, short=True)
