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

import re
from abc import ABC
from enum import unique
from bitcoin.core import lx, b2lx
from bitcoin.core.key import CPubKey
from bitcoin.core.serialize import *
import bitcoin.segwit_addr as bech32

from encode import *
from openseals.parser.field_parser import FieldEnum

"""Generic data types for OpenSeals framework"""

@unique
class Network(FieldEnum):
    """OpenSeals-specific integer identifiers for different supported networks. They differ from magick numbers and
    constants used in Bitcoin core, since the list of networks is different; also serialization format requirements
    reserve `0` value for special meaning in the network field of the proofs, so it can't be used as a valid
    network id

    The class inherits `FieldEnum` type in order to make the value parsable from YAML sources
    """

    bitcoinMainnet = 0x01
    bitcoinTestnet = 0x02
    bitcoinRegnet = 0x03
    bitcoinSegnet = 0x04
    liquidV1 = 0x10

    @classmethod
    def from_str(cls, val: str):
        """Takes string value and returns proper `Network` enum instance.

        :param val: network name in form `blockchain:network`, where `blockchain` may be either 'bitcoin' or 'liquid',
        and network is 'mainnet', 'testnet', 'regnet' and 'signet' for bitcoin and 'v1' for liquid

        :returns: Network enum instance
        :raises ValueError: in case of misformatted or unknown string in `val`
        """

        if ':' in val:
            (blockchain, net) = val.split(':')
            val = blockchain + net.capitalize()
        else:
            raise ValueError(f'network name must be in `blockchain:network` format; found `{val}` instead')

        if val not in cls.__members__:
            raise ValueError(f'unknown blockchain `{blockchain}` or network name `{net}`')

        return cls.__members__[val]


class SemVer(Serializable):
    """Semantic versioning (see semver.org) data structure that can be serializaed and deserialized with consensus
    serialized or read from YAML file
    """

    __slots__ = ['major', 'minor', 'patch']

    def __init__(self, major, minor=None, patch=None):
        if isinstance(major, str) and minor is None and patch is None:
            (self.major, self.minor, self.patch) = [int(c) for c in major.split('.')]
        else:
            self.major = int(major)
            self.minor = int(minor)
            self.patch = int(patch)
        if self.major < 0 or self.major is None:
            raise ValueError(f"Major version number can't be less than zero or None, got {self.major} instead")
        if self.minor < 0 or self.minor is None:
            raise ValueError(f"Major version number can't be less than zero or None, got {self.major} instead")
        if self.patch is None:
            self.patch = 0
        elif self.patch < 0:
            raise ValueError(f"Major version number can't be less than zero, got {self.major} instead")

    def __str__(self):
        return f'{self.major}.{self.minor}.{self.patch}'

    @classmethod
    def from_str(cls, ver: str):
        return SemVer(ver)

    @classmethod
    def stream_deserialize(cls, f, **kwargs):
        major = VarIntSerializer.stream_deserialize(f)
        minor = ser_read(f, 1)
        patch = ser_read(f, 1)
        return cls(major, minor, patch)

    def stream_serialize(self, f, **kwargs):
        VarIntSerializer.stream_serialize(self.major, f)
        f.write(bytes([self.minor]))
        f.write(bytes([self.patch]))


class HashId(ImmutableSerializable, ABC):
    __slots__ = ['bytes', 'bits']

    def __init__(self, data, bits: int):
        if bits not in [160, 256, 512]:
            raise ValueError(f'bits in HashId must be either 160, 256 or 512; found {bits}')

        object.__setattr__(self, 'bits', bits)
        value = None
        if isinstance(data, str):
            match = re.search(re.compile('^([a-z]{1,4})\\d[0-6]?[02-9ac-hj-np-z]+$', re.IGNORECASE), data)
            if match is not None:
                (hrf, value) = bech32.decode(match.group(1), data)
                value = bytes(value)
            elif len(data) is len(self) * 2:
                value = lx(data)
            else:
                raise ValueError(
                    f'HashId requires {len(self)*2}-char hex string or Bech32-encoded string, instead {data} is provided')
        elif isinstance(data, bytes):
            if len(data) is len(self):
                value = data
            else:
                raise ValueError(
                    f'HashId requires {len(self)} bytes for initialization, while only {len(data)} is provided')
        elif isinstance(data, int):
            if data is 0:
                value = bytes([0] * len(self))
            else:
                raise ValueError('HashId may be constructed from int only if its value equals 0')
        else:
            raise ValueError(f'Unknown value for HashId initialization: {data}')
        object.__setattr__(self, 'bytes', value)

    def __str__(self):
        return f'{b2lx(self.bytes)}'

    def __len__(self):
        return int(self.bits/8)

    @classmethod
    def from_str(cls, data: str, bits: int):
        return HashId(data, bits)

    def stream_serialize(self, f, **kwargs):
        f.write(self.bytes)

    @classmethod
    def stream_deserialize(cls, f, **kwargs):
        if 'bits' not in kwargs:
            raise ValueError(
                'HashId.stream_deserialize must be provided with number of hash bits to read (`bits` parameter)')
        bits = kwargs['bits']
        return HashId(f.read(int(bits / 8)), kwargs['bits'])


class Hash160Id(HashId):
    BITS = 160

    def __init__(self, data):
        HashId.__init__(self, data, Hash160Id.BITS)

    @classmethod
    def from_str(cls, data: str, **kwargs):
        super().from_str(data, Hash160Id.BITS)

    @classmethod
    def stream_deserialize(cls, f, **kwargs):
        return super().stream_deserialize(f, bits=Hash160Id.BITS, **kwargs)


class Hash256Id(HashId):
    BITS = 256

    def __init__(self, data):
        HashId.__init__(self, data, Hash256Id.BITS)

    @classmethod
    def from_str(cls, data: str, **kwargs):
        super().from_str(data, Hash256Id.BITS)

    @classmethod
    def stream_deserialize(cls, f, **kwargs):
        return super().stream_deserialize(f, bits=Hash256Id.BITS, **kwargs)


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
    def stream_deserialize(cls, f, **kwargs):
        return cls(ser_read(f, 33))

    def stream_serialize(self, f, **kwargs):
        f.write(self.cpubkey)


class OutPoint(ImmutableSerializable):
    __slots__ = ['txid', 'vout']

    def __init__(self, data, vout=None):
        if isinstance(data, str) and ':' in data and vout is None:
            (txid, vout, *_) = data.split(':')
            txid = bytes(bytearray.fromhex(txid))
        elif isinstance(data, bytes) and vout is not None:
            txid = data
        elif isinstance(data, int) and vout is None:
            (txid, vout) = (None, data)
        else:
            raise ValueError(f"can't reconstruct reansaction outpoint from given arguments `{data}` and `{vout}`")

        if txid is not None and len(txid) is not 32:
            raise ValueError(f'OutPoint must have txid length =32 bytes, got {len(txid)} for `{txid}`')

        try:
            object.__setattr__(self, 'txid', txid)
            object.__setattr__(self, 'vout', int(vout))
        except _:
            raise ValueError('OutPoint can be constructed only from string `txid_hex:vout` or `int`')

    @classmethod
    def stream_deserialize(cls, f, **kwargs):
        short_form = kwargs['short'] if 'short' in kwargs else False
        if short_form:
            vout, flag = FlagVarIntSerializer.stream_deserialize(f)
            txid = ser_read(f, 32) if not flag else None
        else:
            txid = ser_read(f, 32)
            vout = VarIntSerializer.stream_deserialize(f)
        return cls(txid, vout)

    def stream_serialize(self, f, **kwargs):
        short_form = kwargs['short'] if 'short' in kwargs else False
        if self.txid is not None and len(self.txid) is not 32:
            raise ValueError('OutPoint must have a valid txid with length of 32 bytes')
        if short_form:
            flag = self.txid is None
            FlagVarIntSerializer.stream_serialize((self.vout, flag), f)
            f.write(self.txid) if self.txid is not None else ()
        elif self.txid is None:
            raise ValueError('OutPoint can not be zero/None for non-short serialization form')
        else:
            f.write(self.txid)
            VarIntSerializer.stream_serialize(self.vout, f)
