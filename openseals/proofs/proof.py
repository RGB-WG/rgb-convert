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

from enum import unique, IntEnum

from bitcoin.core import ImmutableSerializable, VectorSerializer, VarIntSerializer
import bitcoin.segwit_addr as bech32

from openseals.encode import *
from openseals.data_types import Sha256Id, PubKey, Network, OutPoint
from openseals.parser import *
from openseals.proofs.meta_field import MetaField
from openseals.proofs.seal import Seal
from openseals.schema.schema import Schema


@unique
class ProofFormat(FieldEnum):
    root = 0x00
    upgrade = 0x01
    ordinary = 0x02
    burn = 0x03


class Proof(ImmutableSerializable):

    FIELDS = {
        'ver': FieldParser(int, required=False),
        'format': FieldParser(ProofFormat, required=False, default=ProofFormat.ordinary),
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
            if val is None and self.format is ProofFormat.root:
                raise FieldParseError(FieldParseError.Kind.noRequiredField,
                                      field, 'field must be present the root proof')
            elif val is not None:
                if self.format is ProofFormat.upgrade and field in ['ver', 'schema']:
                    pass
                elif self.format is not ProofFormat.root:
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
        # TODO: check format compliance
        pass

    def bech32_id(self) -> str:
        return bech32.encode('osp', 1, self.GetHash())

    @classmethod
    def stream_deserialize(cls, f, **kwargs):
        pass

    def stream_serialize(self, f, **kwargs):
        # Serializing proof header
        # - version with flag
        ver = self.ver if self.ver is not None else 0
        flag = 0 if self.format is ProofFormat.ordinary or self.format is ProofFormat.burn else 1
        FlagVarIntSerializer.stream_serialize((flag, ver), f)
        # - root proof fields
        if self.format is ProofFormat.root:
            self.schema.stream_serialize(f)
            VarIntSerializer.stream_serialize(self.network.value, f)
            self.root.stream_serialize(f, short_form=False)
        # - version upgrade proof fields
        elif self.format is ProofFormat.upgrade:
            if self.schema is not None:
                self.schema.stream_serialize(f)
            else:
                ZeroBytesSerializer.stream_serialize(32, f)
            ZeroBytesSerializer.stream_serialize(1, f)

        # Serializing proof body
        if self.seals is None:
            ZeroBytesSerializer.stream_serialize(1, f)
        else:
            VectorSerializer.stream_serialize(Seal, self.seals, f, inner_params={'state': False})
            VectorSerializer.stream_serialize(Seal, self.seals, f, inner_params={'state': True})
        VectorSerializer.stream_serialize(MetaField, self.metadata if self.metadata is not None else [], f)

        # Serializing original public key
        if self.pubkey is not None:
            self.pubkey.stream_serialize(f)
        else:
            ZeroBytesSerializer.stream_serialize(1, f)

        # Serializing prubable data
        if self.txid is not None:
            if self.parents is not None:
                f.write(bytes(0x03))
                self.txid.stream_serialize(f)
            else:
                f.write(bytes(0x01))
            VectorSerializer.stream_serialize(Sha256Id, self.parents, f)
        elif self.parents is not None:
            f.write(bytes(0x02))
            VectorSerializer.stream_serialize(Sha256Id, self.parents, f)
        else:
            f.write(bytes(0x00))
