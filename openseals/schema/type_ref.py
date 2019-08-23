from enum import unique
from bitcoin.core.serialize import ImmutableSerializable, VarIntSerializer

from openseals.parser import *


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
        f.write(bytes([[0, 1, 2, 0, 1][self.bounds]]))
        f.write(bytes([[1, 1, 2, 0xFF, 0xFF][self.bounds]]))
