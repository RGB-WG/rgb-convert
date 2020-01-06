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

import struct
from enum import unique
from bitcoin.core.serialize import ser_read, ImmutableSerializable, VarStringSerializer, VarIntSerializer, \
    BytesSerializer

from ..consensus import *
from ..data_types import Hash256Id, Hash160Id, PubKey, HashId
from ..parser import *


class FieldType(ImmutableSerializable):
    @unique
    class Type(FieldEnum):
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
        str = 0x0b
        bytes = 0x0c
        sha256 = 0x10
        sha256d = 0x11
        ripmd160 = 0x12
        hash160 = 0x13
        outpoint = 0x20
        soutpoint = 0x21
        pubkey = 0x30
        ecdsa = 0x31

    FIELDS = {
        'type': FieldParser(Type),
        'name': FieldParser(str)
    }

    __slots__ = list(FIELDS.keys())

    def __init__(self, name: str, tp):
        if isinstance(tp, str):
            for field_name, field in FieldType.FIELDS.items():
                field.parse(self, {'name': name, 'type': tp}, field_name)
        elif isinstance(tp, FieldType.Type):
            object.__setattr__(self, 'name', name)
            object.__setattr__(self, 'type', type)
        else:
            ValueError('type parameter in FieldType constructor must be either string tyoe name or Type enum object')

    def value_from_str(self, s: str):
        if s is None:
            return None
        lut = {
            FieldType.Type.str: lambda x: x,
            FieldType.Type.bytes: lambda x: bytes(x),
            FieldType.Type.sha256: lambda x: Hash256Id(x),
            FieldType.Type.sha256d: lambda x: Hash256Id(x),
            FieldType.Type.ripmd160: lambda x: Hash160Id(x),
            FieldType.Type.hash160: lambda x: Hash160Id(x),
            FieldType.Type.pubkey: lambda x: PubKey(x),
            FieldType.Type.ecdsa: lambda _: None
        }
        result = lut[self.type](s) if self.type in lut.keys() else int(s)
        if result is None:
            raise NotImplementedError()
        return result

    def stream_deserialize_value(self, f):
        lut = {
            FieldType.Type.u8: lambda: ser_read(f, 1),
            FieldType.Type.u16: lambda: struct.unpack(b'<H', ser_read(f, 2))[0],
            FieldType.Type.u32: lambda: struct.unpack(b'<I', ser_read(f, 4))[0],
            FieldType.Type.u64: lambda: struct.unpack(b'<Q', ser_read(f, 8))[0],
            FieldType.Type.i8: lambda: ser_read(f, 1),
            FieldType.Type.i16: lambda: struct.unpack(b'<h', ser_read(f, 2))[0],
            FieldType.Type.i32: lambda: struct.unpack(b'<i', ser_read(f, 4))[0],
            FieldType.Type.i64: lambda: struct.unpack(b'<q', ser_read(f, 8))[0],
            FieldType.Type.vi: lambda: VarIntSerializer.stream_deserialize(f),
            FieldType.Type.fvi: lambda: FlagVarIntSerializer.stream_deserialize(f),
            FieldType.Type.str: lambda: VarStringSerializer.stream_deserialize(f).decode('utf-8'),
            FieldType.Type.bytes: lambda: BytesSerializer.stream_deserialize(f),
            FieldType.Type.sha256: lambda: Hash256Id.stream_deserialize(f),
            FieldType.Type.sha256d: lambda: Hash256Id.stream_deserialize(f),
            FieldType.Type.ripmd160: lambda: Hash160Id.stream_deserialize(f),
            FieldType.Type.hash160: lambda: Hash160Id.stream_deserialize(f),
            FieldType.Type.pubkey: lambda: PubKey.stream_deserialize(f),
            FieldType.Type.ecdsa: lambda: None,
        }
        if self.type in lut.keys():
            return lut[self.type]()
        else:
            raise NotImplementedError()

    def stream_serialize_value(self, value, f):
        if value is None:
            if self.type is FieldType.Type.str or self.type is FieldType.Type.bytes:
                f.write(bytes([0x00]))
            elif self.type is FieldType.Type.fvi:
                f.write(bytes([0xFF]))
            elif self.type in [FieldType.Type.sha256, FieldType.Type.sha256d]:
                f.write(bytes([0]*32))
            elif self.type in [FieldType.Type.ripmd160, FieldType.Type.hash160]:
                f.write(bytes([0]*20))
            elif self.type is FieldType.Type.pubkey:
                f.write(bytes([0x00]))
            elif self.type is FieldType.Type.ecdsa:
                f.write(bytes([0x00]))
            return

        lut = {
            FieldType.Type.u8: lambda x: f.write(bytes([x])),
            FieldType.Type.u16: lambda x: f.write(struct.pack(b'<H', x)),
            FieldType.Type.u32: lambda x: f.write(struct.pack(b'<I', x)),
            FieldType.Type.u64: lambda x: f.write(struct.pack(b'<Q', x)),
            FieldType.Type.i8: lambda x: f.write(bytes([x])),
            FieldType.Type.i16: lambda x: f.write(struct.pack(b'<h', x)),
            FieldType.Type.i32: lambda x: f.write(struct.pack(b'<i', x)),
            FieldType.Type.i64: lambda x: f.write(struct.pack(b'<q', x)),
            FieldType.Type.vi: lambda x: VarIntSerializer.stream_serialize(x, f),
            FieldType.Type.fvi: lambda x: FlagVarIntSerializer.stream_serialize((x, False), f),
            FieldType.Type.str: lambda x: VarStringSerializer.stream_serialize(x.encode('utf-8'), f),
            FieldType.Type.bytes: lambda x: BytesSerializer.stream_serialize(x, f),
            FieldType.Type.sha256: lambda x: x.stream_serealize(f),
            FieldType.Type.sha256d: lambda x: x.stream_serealize(f),
            FieldType.Type.ripmd160: lambda x: x.stream_serealize(f),
            FieldType.Type.hash160: lambda x: x.stream_serealize(f),
            FieldType.Type.pubkey: lambda x: x.stream_serealize(f),
            FieldType.Type.ecdsa: lambda _: None,
        }
        if self.type in lut.keys():
            if self.type in [FieldType.Type.sha256, FieldType.Type.sha256d,
                             FieldType.Type.ripmd160, FieldType.Type.hash160] and not issubclass(value, HashId):
                raise ValueError('in order to serialize hash value you need to provide an instance of HashId class')
            lut[self.type](value)
        else:
            raise NotImplementedError('ECDSA serialization is not implemented')

    @classmethod
    def stream_deserialize(cls, f, **kwargs):
        name = VarStringSerializer.stream_deserialize(f)
        type_val = ser_read(f, 1)
        return FieldType(name, FieldType.Type(type_val))

    def stream_serialize(self, f, **kwargs):
        VarStringSerializer.stream_serialize(self.name.encode('utf-8'), f)
        f.write(bytes([self.type]))
