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


from typing import Any
from bitcoin.core import ImmutableSerializable

from openseals.data_types import Sha256Id, PubKey, Network, OutPoint
from openseals.parser import *
from openseals.proofs.meta_field import MetaField
from openseals.proofs.seal import Seal


class Proof(ImmutableSerializable):
    FIELDS = {
        'ver': FieldParser(int, required=False),
        'schema': FieldParser(Sha256Id, required=False),
        'network': FieldParser(Network, required=False),
        'root': FieldParser(OutPoint, required=False),
        'pubkey': FieldParser(PubKey, required=False),
        'metadata': FieldParser(MetaField, required=False, array=True),
        'seals': FieldParser(Seal, required=False, array=True),
        'parents': FieldParser(Sha256Id, required=False, array=True),
        'txid': FieldParser(Sha256Id, required=False)
    }

    __slots__ = list(FIELDS.keys())

    def __init__(self, schema_obj=None, **kwargs):
        for name, field in Proof.FIELDS.items():
            field.parse(self, kwargs, name)
        for field in ['ver', 'schema', 'network', 'root']:
            val = object.__getattribute__(self, field)
            if val is None and self.is_root():
                raise FieldParseError(FieldParseError.Kind.noRequiredField,
                                      field, 'field must be present the root proof')
            elif val is not None and not self.is_root():
                raise FieldParseError(FieldParseError.Kind.extraField,
                                      field, 'field must be present in root proof only')

    def is_root(self) -> bool:
        return False if self.root is None else True

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        pass
