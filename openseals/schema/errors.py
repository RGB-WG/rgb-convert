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

class SchemaError(Exception):
    __slots__ = ['description']

    def __init__(self, description: str):
        self.description = description

    def __str__(self):
        return self.description


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
