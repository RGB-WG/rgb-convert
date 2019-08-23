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


class Proof(ImmutableSerializable):
    __slots__ = ['ver', 'seals', 'state', 'pubkey', 'metadata', 'parents', 'txid']

    def __init__(self, ver=1, seals=None):
        pass

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
