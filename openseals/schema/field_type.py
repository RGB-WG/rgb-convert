from enum import unique
from bitcoin.core.serialize import ImmutableSerializable, VarStringSerializer

from openseals.parser import *


class FieldType(ImmutableSerializable):
    @unique
    class Type(FieldEnum):
        str = 0x00
        u8 = 0x01
        u16 = 0x02
        u32 = 0x03
        u64 = 0x04
        i8 = 0x05
        i16 = 0x06
        i32 = 0x07
        i64 = 0x08
        vi = 0x09
        fvi = 0x0a
        sha256 = 0x10
        ripmd160 = 0x11
        pub_key = 0x12
        signature = 0x13
        bytes = 0x20

    FIELDS = {
        'type': FieldParser(Type),
        'name': FieldParser(str)
    }

    __slots__ = list(FIELDS.keys())

    def __init__(self, name: str, tp: str):
        for field_name, field in FieldType.FIELDS.items():
            field.parse(self, {'name': name, 'type': tp}, field_name)

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        VarStringSerializer.stream_serialize(self.name.encode('utf-8'), f)
        f.write(bytes([self.type]))
