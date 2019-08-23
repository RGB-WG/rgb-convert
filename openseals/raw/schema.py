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

import logging
from bitcoin.core.serialize import *
from bitcoin.segwit_addr import bech32_encode, convertbits
from ..parser import *
from .types import SemVer, Sha256Id


class SchemaError(Exception):
    pass


class SchemaInternalRefError(SchemaError):
    __slots__ = ['ref_type', 'ref_name', 'section']

    def __init__(self, ref_type: str, ref_name: str, section: str):
        self.ref_type = ref_type
        self.ref_name = ref_name
        self.section = section

    def __str__(self):
        return f'Unable to resolve {self.ref_type} reference inside `{self.section}` named `{self.ref_name}`'


class SchemaValidationError(SchemaError):
    __slots__ = ['description']

    def __init__(self, description: str):
        self.description = description

    def __str__(self):
        return self.description


class TypeRef(ImmutableSerializable):
    @unique
    class Usage(FieldEnum):
        optional = 0x00  # 0-1
        single = 0x01  # =1
        double = 0x02  # =2
        any = 0x03  # 0-∞
        many = 0x04  # 1-∞

    FIELDS = {
        'ref_name': FieldParser(str),
        'bounds': FieldParser(Usage)
    }

    __slots__ = list(FIELDS.keys()) + ['type', 'type_pos']

    def __init__(self, name: str, bounds: str):
        for field_name, field in TypeRef.FIELDS.items():
            field.parse(self, {'ref_name': name, 'bounds': bounds}, field_name)

    def resolve_ref(self, schema_types: list):
        try:
            pos = next(num for num, type in enumerate(schema_types) if type.name == self.ref_name)
            object.__setattr__(self, 'type_pos', pos)
            object.__setattr__(self, 'type', schema_types[pos])
        except StopIteration:
            object.__setattr__(self, 'type_pos', None)
            object.__setattr__(self, 'type', None)

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        VarIntSerializer.stream_serialize(self.type_pos, f)
        f.write(bytes([self.bounds]))


class ProofType(ImmutableSerializable):
    FIELDS = {
        'title': FieldParser(str),
        'unseals': FieldParser(TypeRef, required=False, recursive=True, array=True),
        'fields': FieldParser(TypeRef, recursive=True, array=True),
        'seals': FieldParser(TypeRef, recursive=True, array=True)
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
        VarStringSerializer.stream_serialize(self.title.encode('utf-8'), f)
        VectorSerializer.stream_serialize(TypeRef, self.fields, f)
        VectorSerializer.stream_serialize(TypeRef, [] if self.unseals is None else self.unseals, f)
        VectorSerializer.stream_serialize(TypeRef, self.seals, f)


class SealType(ImmutableSerializable):
    @unique
    class Type(FieldEnum):
        none = 0x00
        balance = 0x01

    FIELDS = {
        'type': FieldParser(Type),
        'name': FieldParser(str)
    }

    __slots__ = list(FIELDS.keys())

    def __init__(self, name: str, tp: str):
        for field_name, field in SealType.FIELDS.items():
            field.parse(self, {'name': name, 'type': tp}, field_name)

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        VarStringSerializer.stream_serialize(self.name.encode('utf-8'), f)
        f.write(bytes([self.type]))


class FieldType(ImmutableSerializable):
    @unique
    class Type(FieldEnum):
        str = 0x00
        u8 = 0x01
        u16 = 0x02
        u32 = 0x03
        u64 = 0x04
        i8 = 0x05
        i16 = 0x06
        i32 = 0x07
        i64 = 0x08
        vi = 0x09
        fvi = 0x0a
        sha256 = 0x10
        ripmd160 = 0x11
        pub_key = 0x12
        signature = 0x13
        bytes = 0x20

    FIELDS = {
        'type': FieldParser(Type),
        'name': FieldParser(str)
    }

    __slots__ = list(FIELDS.keys())

    def __init__(self, name: str, tp: str):
        for field_name, field in FieldType.FIELDS.items():
            field.parse(self, {'name': name, 'type': tp}, field_name)

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        VarStringSerializer.stream_serialize(self.name.encode('utf-8'), f)
        f.write(bytes([self.type]))


class Schema(ImmutableSerializable):
    FIELDS = {
        'name': FieldParser(str),
        'schema_ver': FieldParser(SemVer),
        'prev_schema': FieldParser(Sha256Id),
        'field_types': FieldParser(FieldType, recursive=True, array=True),
        'seal_types': FieldParser(SealType, recursive=True, array=True),
        'proof_types': FieldParser(ProofType, recursive=True, array=True),
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
        return bech32_encode('oss', convertbits(self.GetHash(), 8, 5))

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
