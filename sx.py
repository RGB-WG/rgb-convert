#!/usr/bin/env python3

# This file is a part of Python OpenSeals library tools
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


import re
import sys
import logging
from pprint import pprint

import yaml
import click

from openseals.raw.schema import *

__author__ = "Dr Maxim Orlovsky"


@click.group()
def main():
    """
    Simple CLI for working with OpenSeals proof files
    """
    pass


@main.command()
@click.argument('file')
@click.option('--format', '-f')
def validate(file: str, format: str):
    """
    Reads file containing a proof, schema or a proof history and validates its consistency.
    File can have YAML or binary serialization format. The format is guessed by file extension: YAML files must have
    .yaml or .yml extension; other file extension are considered to be binary. This can be modified with -t or
    --filetype command-line option, which can take either 'YAML' or 'binary' values
    """
    logging.info(f'Validating schema from `{file}`:')
    if format is None:
        format = "yaml" if re.search("\\.ya?ml$", file.lower()) is not None else "binary"
    elif format.lower() == "yaml" or format.lower() == "binary":
        format = format.lower()
    else:
        sys.exit("Wrong value for --format or -f argument: accepted values are 'yaml' and 'binary'")

    logging.debug(f'- applied format is `{format}`')
    logging.debug('- reading data with this format')
    with open(file) as f:
        data = yaml.safe_load(f)

    logging.debug('- parsing data')
    schema = Schema(**data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
