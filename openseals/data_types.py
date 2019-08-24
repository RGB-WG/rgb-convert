import re
import struct
from enum import unique
from bitcoin.core import lx, b2lx
from bitcoin.core.key import CPubKey
from bitcoin.core.serialize import *
import bitcoin.segwit_addr as bech32

from openseals.parser.field_parser import FieldEnum


@unique
class Network(FieldEnum):
    bitcoinMainnet = 0x00
    bitcoinTestnet = 0x01
    bitcoinRegnet = 0x02
    bitcoinSegnet = 0x03
    liquidV1 = 0x10

    @classmethod
    def from_str(cls, val: str):
        if ':' in val:
            (blockchain, net) = val.split(':')
            val = blockchain + net.capitalize()
        return cls.__members__[val]


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
            match = re.search(re.compile('^(oss|osp|bc|tb)\\d[0-6]?[02-9ac-hj-np-z]+$', re.IGNORECASE), data)
            if match is not None:
                (hrf, value) = bech32.decode(match.group(1), data)
                value = bytes(value)
            elif len(data) is 64:
                value = lx(data)
            else:
                raise ValueError(
                    f'Sha256Id requires 64-char hex string or bech32-encoded string, instead {data} is provided')
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


class PubKey(ImmutableSerializable):
    __slots__ = ['cpubkey']

    def __init__(self, data):
        if isinstance(data, str):
            data = bytearray.fromhex(data)
        if isinstance(data, bytearray):
            data = bytes(data)
        if not isinstance(data, bytes):
            raise ValueError('PubKey can be constructed only from either hex string, bytearray or byte data')
        object.__setattr__(self, 'cpubkey', CPubKey(data))

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        f.write(self.cpubkey)


class OutPoint(ImmutableSerializable):
    __slots__ = ['txid', 'vout']

    def __init__(self, data):
        if isinstance(data, str) and ':' in data:
            (txid, vout, *_) = data.split(':')
            txid = bytes(bytearray.fromhex(txid))
            if len(txid) is not 32:
                raise ValueError(f'OutPoint must have txid length =32 bytes, got {len(txid)} for `{txid}`')
        else:
            (txid, vout) = (None, data)
        try:
            object.__setattr__(self, 'txid', txid)
            object.__setattr__(self, 'vout', int(vout))
        except:
            raise ValueError('OutPoint can be constructed only from string `txid_hex:vout` or `int`')

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f, short_form=False):
        if self.txid is not None and len(self.txid) is not 32:
            raise ValueError('OutPoint must have a valid txid with length of 32 bytes')
        if short_form:
            VarIntSerializer.stream_serialize(self.vout, f)
            f.write(self.txid) if self.txid is not None else ()
        elif self.txid is None:
            raise ValueError('OutPoint can not be zero/None for non-short serialization form')
        else:
            f.write(self.txid)
            VarIntSerializer.stream_serialize(self.vout, f)
