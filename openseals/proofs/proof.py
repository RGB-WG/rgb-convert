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


from bitcoin.core import ImmutableSerializable, VectorSerializer
from bitcoin.segwit_addr import bech32_encode, convertbits

from openseals.data_types import Sha256Id, PubKey, Network, OutPoint
from openseals.parser import *
from openseals.proofs.meta_field import MetaField
from openseals.proofs.seal import Seal
from openseals.schema.schema import Schema


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

    __slots__ = list(FIELDS.keys()) + ['schema_obj']

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
        if (self.parents is not None and self.txid is None) or (self.parents is None and self.txid is not None):
            raise FieldParseError(FieldParseError.Kind.noRequiredField,
                                  'parents' if self.parents is None else 'txid',
                                  'both `parents` and `txid` fields must be present for non-pruned proof data')
        if isinstance(schema_obj, Schema):
            self.resolve_schema(schema_obj)

    def resolve_schema(self, schema: Schema):
        object.__setattr__(self, 'schema_obj', schema)
        [field.resolve_schema(schema) for field in self.metadata]
        [seal.resolve_schema(schema) for seal in self.seals]

    def validate(self):
        pass

    def is_root(self) -> bool:
        return False if self.root is None else True

    def is_pruned(self) -> bool:
        return self.txid is None and self.parents is None

    def bech32_id(self) -> str:
        return bech32_encode('osp', convertbits(self.GetHash(), 8, 5))

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        if self.is_root():
            f.write(bytes([self.ver | 0x80]))
            self.schema.stream_serialize(f)
            f.write(bytes([self.network]))
            self.root.stream_serialize(f)
        else:
            f.write(bytes([(self.ver if self.ver is not None else 0x00) & 0x7F]))

        VectorSerializer.stream_serialize(MetaField, self.metadata if self.metadata is not None else [], f)
        VectorSerializer.stream_serialize(Seal, self.seals if self.seals is not None else [], f)

        if self.pubkey is None:
            f.write(b'\x00')
        else:
            f.write(b'\x01')
            self.pubkey.stream_serialize(f)

        if not self.is_pruned():
            VectorSerializer.stream_serialize(Sha256Id, self.parents, f)
            self.txid.stream_serialize(f)
