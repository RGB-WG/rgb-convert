import struct

from bitcoin.core import Serializer, ser_read


class FlagVarIntSerializer(Serializer):
    """Serialization of flag-prefixed variable length ints"""
    @classmethod
    def stream_serialize(cls, val, f):
        (i, flag) = val
        mask = 0x80 if flag is True else 0
        if i < 0:
            raise ValueError('FlagVarInt must be a non-negative integer')
        elif i < 0xfc:
            f.write(bytes([i]))
        elif i <= 0xff:
            f.write(bytes(0x7c & mask))
            f.write(bytes([i]))
        elif i <= 0xffff:
            f.write(bytes(0x7d & mask))
            f.write(struct.pack(b'<H', i))
        elif i <= 0xffffffff:
            f.write(bytes(0x7e & mask))
            f.write(struct.pack(b'<I', i))
        else:
            f.write(bytes(0x7f & mask))
            f.write(struct.pack(b'<Q', i))

    @classmethod
    def stream_deserialize(cls, f):
        r = ser_read(f, 1)[0]
        mask = 0x80 & r
        flag = True if mask is 0x80 else False
        r = r & 0x7f
        if r < 0x7c:
            return r, flag
        elif r == 0x7c:
            return ser_read(f, 1)[0], flag
        elif r == 0xfd:
            return struct.unpack(b'<H', ser_read(f, 2))[0]
        elif r == 0xfe:
            return struct.unpack(b'<I', ser_read(f, 4))[0]
        else:
            return struct.unpack(b'<Q', ser_read(f, 8))[0]


class ZeroBytesSerializer(Serializer):
    """Serialization of zero bytes stream"""
    @classmethod
    def stream_serialize(cls, val, f):
        f.write(bytes([0]*val))

    @classmethod
    def stream_deserialize(cls, f):
        raise RuntimeError('ZeroBytesSerializer.stream_deserialize should never be called')
