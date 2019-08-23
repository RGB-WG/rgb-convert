from enum import unique
from bitcoin.core.serialize import ImmutableSerializable, VarStringSerializer

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

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        VarStringSerializer.stream_serialize(self.name.encode('utf-8'), f)
        f.write(bytes([self.type]))
