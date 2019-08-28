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

from bitcoin.core.serialize import ImmutableSerializable, VarStringSerializer, VectorSerializer
import bitcoin.segwit_addr as bech32

from . import *
from openseals.data_types import SemVer, Sha256Id
from openseals.parser import *


class Schema(ImmutableSerializable):
    FIELDS = {
        'name': FieldParser(str),
        'schema_ver': FieldParser(SemVer),
        'prev_schema': FieldParser(Sha256Id),
        'field_types': FieldParser(FieldType, array=True),
        'seal_types': FieldParser(SealType, array=True),
        'proof_types': FieldParser(ProofType, array=True),
    }

    __slots__ = list(FIELDS.keys())

    def __init__(self, **kwargs):
        for name, field in Schema.FIELDS.items():
            field.parse(self, kwargs, name)

    def resolve_refs(self):
        for proof_type in self.proof_types:
            proof_type.resolve_refs(self)

    def validate(self):
        if len(self.proof_types) is 0:
            raise SchemaValidationError('Schema contains zero proof types defined')
        for proof_type in self.proof_types[1:]:
            if proof_type.unseals is None:
                raise SchemaValidationError(
                    f'No `unseals` specified for `{proof_type.title}`, the field is required for all non-root proofs')

    def bech32_id(self) -> str:
        return bech32.encode('sm', 1, self.GetHash())

    @classmethod
    def stream_deserialize(cls, f):
        name = VarStringSerializer.deserialize(f)
        #return Schema(
        #    name=name,
        #    schema_ver=schema_ver,
        #    prev_schema=prev_schema,
        #    field_types=field_types,
        #    seal_types=seal_types,
        #    proof_types=proof_types
        #)

    def stream_serialize(self, f):
        VarStringSerializer.stream_serialize(self.name.encode('utf-8'), f)
        self.schema_ver.stream_serialize(f)
        self.prev_schema.stream_serialize(f)
        VectorSerializer.stream_serialize(FieldType, self.field_types, f)
        VectorSerializer.stream_serialize(SealType, self.seal_types, f)
        VectorSerializer.stream_serialize(ProofType, self.proof_types, f)
