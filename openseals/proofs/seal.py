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


from bitcoin.core import ImmutableSerializable

from openseals.parser import *
from openseals.data_types import OutPoint
from openseals.schema.schema import Schema


class Seal(ImmutableSerializable):
    FIELDS = {
        'type': FieldParser(str),
        'outpoint': FieldParser(OutPoint),
        'amount': FieldParser(int, required=False)
    }

    __slots__ = list(FIELDS.keys()) + ['seal_type']

    def __init__(self, schema_obj=None, **kwargs):
        for field_name, field in Seal.FIELDS.items():
            field.parse(self, kwargs, field_name)
        if isinstance(schema_obj, Schema):
            self.resolve_ref(schema_obj.seal_types)

    def resolve_ref(self, seal_types: list):
        try:
            pos = next(num for num, type in enumerate(seal_types) if type.name == self.type)
            object.__setattr__(self, 'seal_type', seal_types[pos])
        except StopIteration:
            object.__setattr__(self, 'seal_type', None)

    @classmethod
    def stream_deserialize(cls, f):
        pass

    def stream_serialize(self, f):
        pass
