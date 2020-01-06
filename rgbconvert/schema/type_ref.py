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

from enum import unique
from bitcoin.core.serialize import ImmutableSerializable, VarIntSerializer, VectorSerializer, ser_read

from ..data_types import PubKey
from ..parser import *
from ..schema import FieldType, SchemaError


class TypeRef(ImmutableSerializable):
    @unique
    class Usage(FieldEnum):
        optional = 0x00  # 0-1
        single = 0x01  # =1
        double = 0x02  # =2
        any = 0x03  # 0-∞
        many = 0x04  # 1-∞

        def min(self) -> int:
            return [0, 1, 2, 0, 1][self.value]

        def max(self) -> int:
            return [1, 1, 2, 0xFF, 0xFF][self.value]

        def is_fixed(self) -> bool:
            return self.min() is self.max() and self.min() > 0

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

    def stream_deserialize_value(self, f):
        if self.bounds is TypeRef.Usage.single:
            value = self.type.stream_deserialize_value(f)
        elif self.bounds.is_fixed():
            value = [self.type.stream_deserialize_value(f) for n in range(0, self.bounds.min())]
        elif self.bounds is TypeRef.Usage.optional:
            if self.type.type is FieldType.Type.pubkey:
                key = ser_read(f, 1)
                if key[0] is 0:
                    return None
                data = key + ser_read(f, 32)
                return PubKey.deserialize(data)
            elif self.type.type is FieldType.Type.ecdsa:
                key = ser_read(f, 1)
                if key[0] is 0:
                    return None
                raise NotImplementedError('ECDSA deserealization is not implemented')

            try:
                value = self.type.stream_deserialize_value(f)
            except BaseException as ex:
                # due to some strange bug, python 3 is unable to capture SeparatorByteSignal exception by its type,
                # and `isinstance(ex, SeparatorByteSignal)` returns False as well :(
                # so we have to capture generic exception and re-raise if it is not SeparatorByteSignal, which
                # can be determined only by the presence of its method
                if not callable(getattr(ex, "is_eof", None)):
                    raise
                if ex.is_eof():
                    # -- met 0xFF separator byte, indicating absent value
                    value = None
                else:
                    raise

            if self.type.type is FieldType.Type.fvi:
                pass
            elif self.type.type is FieldType.Type.str:
                value = None if value is b'\x00' or len(value) is 0 else value
            elif self.type.type is FieldType.Type.bytes:
                value = None if len(value) is 0 else value
            elif self.type.type in [FieldType.Type.sha256, FieldType.Type.sha256d]:
                value = None if value is bytes([0] * 32) else value
            elif self.type.type in [FieldType.Type.ripmd160, FieldType.Type.hash160]:
                value = None if value is bytes([0] * 20) else value
            else:
                raise SchemaError(f'optional fields can be only of `str`, `fvi`, `bytes` and complex types')
        else:
            no = VarIntSerializer.stream_deserialize(f)
            value = [self.type.stream_deserialize_value(f) for n in range(0, no)]

        return value

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        VarIntSerializer.stream_serialize(self.type_pos, f)
        f.write(bytes([self.bounds.min()]))
        f.write(bytes([self.bounds.max()]))
