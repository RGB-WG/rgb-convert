# This file a is part of Python OpenSeals library
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


from bitcoin.core import ImmutableSerializable

from openseals.data_types import Sha256Id
from openseals.parser import *


class Proof(ImmutableSerializable):
    FIELDS = {
        'ver': FieldParser(int, required=False),
        'schema': FieldParser(str, required=False),
        'network': FieldParser(str, required=False),
        'pubkey': FieldParser(str, required=False),
        # 'metadata': FieldParser(ProofMeta, required=False, array=True),
        # 'seals': FieldParser(Seal, required=False, array=True),
        'parents': FieldParser(str, required=False, array=True),
        'txid': FieldParser(str, required=False)
    }

    __slots__ = list(FIELDS.keys())

    def __init__(self, schema=None, **kwargs):
        for name, field in Proof.FIELDS.items():
            field.parse(self, kwargs, name)

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        pass


class RootProof(Proof):
    __slots__ = ['root', 'schema', 'network']

    def __init__(self, ver=1, seals=None):
        Proof.__init__(self, ver, seals)
        if seals is None:
            seals = []

    def stream_serialize(self, f):
        pass
