import struct
from enum import unique
from bitcoin.core.serialize import ImmutableSerializable, VarStringSerializer, VarIntSerializer

from openseals.data_types import Sha256Id, PubKey
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

    def value_from_str(self, s: str):
        lut = {
            FieldType.Type.str: lambda x: x,
            FieldType.Type.sha256: lambda x: Sha256Id(x),
            FieldType.Type.ripmd160: lambda _: None,
            FieldType.Type.pub_key: lambda x: PubKey(x),
            FieldType.Type.signature: lambda _: None,
            FieldType.Type.bytes: lambda x: bytes(x),
        }
        result = lut[self.type](s) if self.type in lut.keys() else int(s)
        if result is None:
            raise NotImplementedError()
        return result

    def stream_serialize_value(self, value, f):
        lut = {
            FieldType.Type.str: lambda x: VarStringSerializer.stream_serialize(x.encode('utf-8'), f),
            FieldType.Type.u8: lambda x: f.write(bytes([x])),
            FieldType.Type.u16: lambda x: f.write(struct.pack(b'<H', x)),
            FieldType.Type.u32: lambda x: f.write(struct.pack(b'<I', x)),
            FieldType.Type.u64: lambda x: f.write(struct.pack(b'<Q', x)),
            FieldType.Type.i8: lambda x: f.write(bytes([x])),
            FieldType.Type.i16: lambda x: f.write(struct.pack(b'<H', x)),
            FieldType.Type.i32: lambda x: f.write(struct.pack(b'<I', x)),
            FieldType.Type.i64: lambda x: f.write(struct.pack(b'<Q', x)),
            FieldType.Type.vi: lambda x: VarIntSerializer.stream_serialize(x, f),
        }
        if self.type in lut.keys():
            lut[self.type](value)
        else:
            raise NotImplementedError()

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        VarStringSerializer.stream_serialize(self.name.encode('utf-8'), f)
        f.write(bytes([self.type]))
