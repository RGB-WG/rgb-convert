from bitcoin.core import lx, b2lx
from bitcoin.core.serialize import *


class SemVer(Serializable):
    __slots__ = ['major', 'minor', 'patch']

    def __init__(self, major, minor=None, patch=None):
        if isinstance(major, str):
            (self.major, self.minor, self.patch) = [int(c) for c in major.split('.')]
        else:
            self.major = major
            self.minor = minor
            self.patch = patch

    def __str__(self):
        return f'{self.major}.{self.minor}.{self.patch}'

    @classmethod
    def from_str(self, ver: str):
        return SemVer(ver)

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        VarIntSerializer.stream_serialize(self.major, f)
        f.write(bytes([self.minor]))
        f.write(bytes([self.patch]))


class Sha256Id(ImmutableSerializable):
    __slots__ = ['bytes']

    def __init__(self, data):
        value = None
        if isinstance(data, str):
            value = lx(data)
            if len(value) is not 32:
                raise ValueError(f'Sha256Id requires 32 bytes for initialization, while only {len(value)} is provided')
        elif isinstance(data, bytes):
            if len(data) is 32:
                value = data
            else:
                raise ValueError(f'Sha256Id requires 32 bytes for initialization, while only {len(data)} is provided')
        elif isinstance(data, int):
            if data is 0:
                value = bytes([0] * 32)
            else:
                raise ValueError('Sha256Id may be constructed from int only if its value equals 0')
        else:
            raise ValueError(f'Unknown value for Sha256Id initialization: {data}')
        object.__setattr__(self, 'bytes', value)

    def __str__(self):
        return f'{b2lx(self.bytes)}'

    @classmethod
    def from_str(self, ver: str):
        return Sha256Id(ver)

    @classmethod
    def stream_deserialize(cls, f):
        return Sha256Id(f.read(32))

    def stream_serialize(self, f):
        f.write(self.bytes)
