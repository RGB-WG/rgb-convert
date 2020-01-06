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

from enum import Enum, unique


class FieldParseError(Exception):
    """Errors raised due to incomplete or misstructured fields in source file (YAML etc)"""

    @unique
    class Kind(Enum):
        noRequiredField = "required field is not present"
        wrongFieldType = "wrong field type"
        wrongEnumValue = "wrong enum value"
        extraField = "extra field that must be absent"

    __slots__ = ['kind', 'field_name', 'details']

    def __init__(self, kind: Kind, field_name: str, details=None):
        self.kind = kind
        self.field_name = field_name
        self.details = details

    def __str__(self):
        msg = f"Unable to parse field `{self.field_name}`: {self.kind.value}"
        if self.details is not None:
            msg = msg + f" ({self.details})"
        return msg

