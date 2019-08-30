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

from .errors import FieldParseError
from .field_parser import FieldEnum, FieldParser


class StructureSerializable:
    """Allows to serialize data to YAML, JSON and other structured formats"""

    @classmethod
    def structure_deserialize(cls, data: dict, **kwargs):
        return cls.__init__(**data)

    def structure_serialize(self, **kwargs):
        NotImplementedError('Child classes must implement `structure_serialize` method')


__all__ = [
    'FieldEnum',
    'FieldParser',
    'FieldParseError',
    'StructureSerializable'
]
