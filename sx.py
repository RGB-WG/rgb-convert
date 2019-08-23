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

import yaml
import click

from openseals.schema.schema import *

__author__ = "Dr Maxim Orlovsky <orlovsky@pandoracore.com>"


@click.group()
def main():
    """
    Simple CLI for working with OpenSeals proof files
    """
    pass


@main.command()
@click.argument('file')
@click.option('--format', '-f')
def schema_validate(file: str, format: str) -> Schema:
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

    logging.info(f'- applied format is `{format}`')
    logging.info('- reading data with this format')
    with open(file) as f:
        data = yaml.safe_load(f)

    logging.info('- parsing data')
    schema = Schema(**data)

    logging.info('- resolving internal references')
    schema.resolve_refs()

    logging.info('- validating schema')
    schema.validate()

    logging.info(f'Schema `{schema.name}`, version {schema.schema_ver} is correct')
    return schema


@main.command()
@click.argument('infile')
@click.argument('outfile')
def schema_transcode(infile: str, outfile: str):
    """Transcodes schema file into another format"""
    logging.info(f'Transcoding schema from `{infile}` to `{outfile}`:')

    logging.info('- loading data')
    with open(infile) as f:
        data = yaml.safe_load(f)
    schema = Schema(**data)
    schema.resolve_refs()

    logging.info('- serializing data')
    with open(outfile, 'wb') as f:
        schema.stream_serialize(f)
        pos = f.tell()
    logging.info(
        f'''Schema `{schema.name}`, version {schema.schema_ver} was transcoded into `{outfile}`; {pos} byes written,
          schema hash is {schema.bech32_id()}''')


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    main()
