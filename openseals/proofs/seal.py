# This file is a part of Python OpenSeals library
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


class Seal(ImmutableSerializable):
    __slots__ = ['vout']

    def __init__(self, vout=0xffffffff):
        self.vout = vout

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        pass


class VoutSeal(Seal):
    pass


class UTXOSeal(Seal):
    __slots__ = ['txid']

    def __init__(self, txid=b'\x00'*32, vout=0xffffffff):
        Seal.__init__(self, vout)
        self.txid = txid

    def stream_serialize(self, f):
        pass
