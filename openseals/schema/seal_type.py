from enum import unique
from bitcoin.core.serialize import ImmutableSerializable, VarStringSerializer, VarIntSerializer

from openseals.parser import *


class SealType(ImmutableSerializable):
    @unique
    class Type(FieldEnum):
        none = 0x00
        balance = 0x01

    FIELDS = {
        'type': FieldParser(Type),
        'name': FieldParser(str)
    }

    __slots__ = list(FIELDS.keys())

    def __init__(self, name: str, tp: str):
        for field_name, field in SealType.FIELDS.items():
            field.parse(self, {'name': name, 'type': tp}, field_name)

    def state_from_dict(self, data: dict):
        if self.type is SealType.Type.balance:
            return int(data['amount'])
        else:
            return None

    def stream_serialize_state(self, state, f):
        if self.type is SealType.Type.balance:
            VarIntSerializer.stream_serialize(state, f)

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        VarStringSerializer.stream_serialize(self.name.encode('utf-8'), f)
        f.write(bytes([self.type]))
