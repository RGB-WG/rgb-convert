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
from bitcoin.core import ImmutableSerializable
from ..parse import *


class MetaField(ImmutableSerializable):
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
        for field_name, field in MetaField.FIELDS.items():
            field.parse(self, {'name': name, 'type': tp}, field_name)

        # data = list(kwargs.items())
        # if len(data) is not 1:
        #     raise FieldParseError(FieldParseError.Kind.wrongFieldType, 'meta_field', f'`{data}`')
        # data = data[0]
        # MetaField.FIELDS['name'].parse(self, {'name': data[0]}, 'name')
        # try:
        #     object.__setattr__(self, 'type', MetaField.Type.from_str(data[1]))
        # except KeyError as err:
        #     raise FieldParseError(FieldParseError.Kind.wrongEnumValue, data[0], f'`{data[1]}`')

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        pass


class Schema(ImmutableSerializable):
    FIELDS = {
        'name': FieldParser(str),
        'schema_ver': FieldParser(str),
        'prev_schema': FieldParser(str),
        'meta_fields': FieldParser(MetaField, recursive=True, array=True),
        # 'seal_types': FieldParser(str, True),
        # 'proof_types': FieldParser(str, True),
    }

    __slots__ = list(FIELDS.keys())

    def __init__(self, **kwargs):
        logging.debug('-- parsing root schema')
        for name, field in Schema.FIELDS.items():
            field.parse(self, kwargs, name)

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        pass
