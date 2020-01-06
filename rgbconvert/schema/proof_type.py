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

from bitcoin.core.serialize import ImmutableSerializable, VarStringSerializer, VectorSerializer

from .type_ref import TypeRef
from .errors import *
from ..parser import *


class ProofType(ImmutableSerializable):
    FIELDS = {
        'name': FieldParser(str),
        'unseals': FieldParser(TypeRef, required=False, array=True),
        'fields': FieldParser(TypeRef, array=True),
        'seals': FieldParser(TypeRef, array=True)
    }

    __slots__ = list(FIELDS.keys())

    def __init__(self, **kwargs):
        for name, field in ProofType.FIELDS.items():
            field.parse(self, kwargs, name)

    def resolve_refs(self, schema):
        for meta_field in self.fields:
            meta_field.resolve_ref(schema.field_types)
            if meta_field.type is None:
                raise SchemaInternalRefError(ref_type='field', ref_name=meta_field.ref_name, section='fields')
        for seal in self.seals:
            seal.resolve_ref(schema.seal_types)
            if seal.type is None:
                raise SchemaInternalRefError(ref_type='seal', ref_name=seal.ref_name, section='seals')
        if self.unseals is not None:
            for seal in self.unseals:
                seal.resolve_ref(schema.seal_types)
                if seal.type is None:
                    raise SchemaInternalRefError(ref_type='seal', ref_name=seal.ref_name, section='unseals')

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        VarStringSerializer.stream_serialize(self.name.encode('utf-8'), f)
        VectorSerializer.stream_serialize(TypeRef, self.fields, f)
        VectorSerializer.stream_serialize(TypeRef, [] if self.unseals is None else self.unseals, f)
        VectorSerializer.stream_serialize(TypeRef, self.seals, f)
