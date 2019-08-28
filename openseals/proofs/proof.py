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
import io
from enum import unique
from functools import reduce

from bitcoin.core.serialize import ImmutableSerializable, VectorSerializer, VarIntSerializer, BytesSerializer, ser_read
import bitcoin.segwit_addr as bech32

from openseals.encode import *
from openseals.data_types import Hash256Id, PubKey, Network, OutPoint
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
        'schema': FieldParser(Hash256Id, required=False),
        'network': FieldParser(Network, required=False),
        'root': FieldParser(OutPoint, required=False),
        'pubkey': FieldParser(PubKey, required=False),
        'fields': FieldParser(MetaField, required=False, array=True),
        'seals': FieldParser(Seal, required=False, array=True),
        'parents': FieldParser(Hash256Id, required=False, array=True),
        'txid': FieldParser(Hash256Id, required=False)
    }

    __slots__ = list(FIELDS.keys()) + ['schema_obj', 'state', 'metadata']

    def __init__(self, schema_obj=None, **kwargs):
        if 'format' in kwargs and isinstance(kwargs['format'], ProofFormat):
            [object.__setattr__(self, attr, value) for attr, value in kwargs]
            object.__setattr__(self, 'schema_obj', schema_obj)
            object.__setattr__(self, 'state', kwargs['state'] if 'state' in kwargs else None)
            object.__setattr__(self, 'metadata', kwargs['metadata'] if 'metadata' in kwargs else None)
            return

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

        object.__setattr__(self, 'state', None)
        object.__setattr__(self, 'metadata', None)

        if isinstance(schema_obj, Schema):
            self.resolve_schema(schema_obj)

    def resolve_schema(self, schema: Schema):
        object.__setattr__(self, 'schema_obj', schema)
        [field.resolve_schema(schema) for field in self.fields]
        [seal.resolve_schema(schema) for seal in self.seals]

    def validate(self):
        # TODO: check format compliance
        pass

    def bech32_id(self) -> str:
        return bech32.encode('pf', 1, self.GetHash())

    @classmethod
    def stream_deserialize(cls, f, **kwargs):
        schema_obj = kwargs['schema_obj'] if 'schema_obj' not in kwargs else None
        if not isinstance(schema_obj, Schema):
            raise ValueError(f'`schema_obj` parameter must be of Schema type; got `{schema_obj}` instead')

        # Deserialize proof header
        # - version with flag
        (ver, flag) = FlagVarIntSerializer.stream_deserialize(f)
        # - fields common for root and upgrade proofs
        if flag:
            schema = Hash256Id.stream_deserialize(f)
            network = VarIntSerializer.stream_deserialize(f)
            if network is 0x00:
                format = ProofFormat.upgrade
            # - root-specific fields
            else:
                format = ProofFormat.root
                root = OutPoint.stream_deserialize(f, short=False)
        else:
            format = ProofFormat.ordinary

        # Deserialize proof body
        seals = VectorSerializer.stream_deserialize(Seal, f, inner_params={'state': False})
        if len(seals) is 0:
            format = ProofFormat.burn

        if schema_obj:
            _ = VarIntSerializer.stream_deserialize(f)
            [seal.stream_deserialize_state(f, schema=schema_obj) for seal in seals]
            _ = VarIntSerializer.stream_deserialize(f)
            fields = [field_type.stream_deserealize_value(f) for field_type in schema_obj.field_types]
            state = None
            metadata = None
        else:
            state = BytesSerializer.stream_deserialize(f)
            metadata = BytesSerializer.stream_deserialize(f)
            fields = None

        # Deserialize original public key
        pkcode = ser_read(f, 1)
        if pkcode is 0x00:
            pubkey = None
        else:
            buf = [pkcode] + ser_read(f, 32)
            pubkey = PubKey.deserialize(buf)

        # Deserialize prunable data
        try:
            pruned_flag = ser_read(f, 1)
        except EOFError:
            pruned_flag = 0x00

        if pruned_flag & 0x01 > 0:
            txid = Hash256Id.stream_deserialize(f)
        if pruned_flag & 0x02 > 0:
            parents = VectorSerializer.stream_deserialize(Hash256Id, f)

        return Proof(
            schema_obj=schema_obj,
            ver=ver, format=format, schema=schema, network=network, root=root, pubkey=pubkey,
            fields=fields, seals=seals, txid=txid, parents=parents, metadata=metadata, state=state
        )

    def stream_serialize(self, f, **kwargs):
        # Serialize proof header
        # - version with flag
        ver = self.ver if self.ver is not None else 0
        flag = self.format is ProofFormat.root or self.format is ProofFormat.upgrade
        FlagVarIntSerializer.stream_serialize((ver, flag), f)
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

        # Serialize proof body
        if self.seals is None:
            # - if this is proof of burn, serialize double zero byte to indicate zero seals and no sealed state
            ZeroBytesSerializer.stream_serialize(2, f)
        else:
            # - otherwise, write seals and state information
            VectorSerializer.stream_serialize(Seal, self.seals, f, inner_params={'state': False})
            length = reduce((lambda acc, seal: acc + len(seal.serialize({'state': True}))), [0] + self.seals)
            VarIntSerializer.stream_serialize(length, f)
            [seal.stream_serialize(f, state=True) for seal in self.seals]

        # - now write all metafields
        length = reduce((lambda acc, field: acc + len(field.serialize())), [0] + self.fields)
        VarIntSerializer.stream_serialize(length, f)
        [field.stream_serialize(f) for field in self.fields]

        # Serialize original public key
        if self.pubkey is not None:
            self.pubkey.stream_serialize(f)
        else:
            ZeroBytesSerializer.stream_serialize(1, f)

        # Serialize prunable data
        if self.txid is not None:
            if self.parents is not None:
                f.write(bytes(0x03))
                self.txid.stream_serialize(f)
            else:
                f.write(bytes(0x01))
            VectorSerializer.stream_serialize(Hash256Id, self.parents, f)
        elif self.parents is not None:
            f.write(bytes(0x02))
            VectorSerializer.stream_serialize(Hash256Id, self.parents, f)
        else:
            f.write(bytes(0x00))
