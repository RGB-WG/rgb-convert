from bitcoin.core.serialize import ImmutableSerializable, VarStringSerializer, VectorSerializer

from .type_ref import TypeRef
from .errors import *
from openseals.parser import *


class ProofType(ImmutableSerializable):
    FIELDS = {
        'title': FieldParser(str),
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
        VarStringSerializer.stream_serialize(self.title.encode('utf-8'), f)
        VectorSerializer.stream_serialize(TypeRef, self.fields, f)
        VectorSerializer.stream_serialize(TypeRef, [] if self.unseals is None else self.unseals, f)
        VectorSerializer.stream_serialize(TypeRef, self.seals, f)
