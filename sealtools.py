#!/usr/bin/env python3

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


import re
import sys
import logging

import yaml
import click

from openseals.schema.schema import *
from openseals.proofs.proof import *

__author__ = "Dr Maxim Orlovsky <orlovsky@pandoracore.com>"


@click.group()
def main():
    """
    Simple CLI for working with OpenSeals proof files
    """
    pass


def guess_format(file: str, kwargs: dict) -> str:
    format = kwargs['format'] if 'format' in kwargs else None
    if format is None:
        format = "yaml" if re.search("\\.ya?ml$", file.lower()) is not None else "binary"
    elif format.lower() == "yaml" or format.lower() == "binary":
        format = format.lower()
    else:
        sys.exit("Wrong value for --format or -f argument: accepted values are 'yaml' and 'binary'")
    return format


def load_shema(file: str) -> Schema:
    logging.info(f'- loading schema data from `{file}`')
    with open(file) as f:
        data = yaml.safe_load(f)
    schema = Schema(**data)
    schema.resolve_refs()
    return schema


@main.command()
@click.argument('file')
@click.option('--format', '-f')
def schema_validate(file: str, **kwargs) -> Schema:
    """
    Reads file containing a proof, schema or a proof history and validates its consistency.
    File can have YAML or binary serialization format. The format is guessed by file extension: YAML files must have
    .yaml or .yml extension; other file extension are considered to be binary. This can be modified with -t or
    --filetype command-line option, which can take either 'YAML' or 'binary' values
    """
    logging.info(f'Validating schema from `{file}`:')
    format = guess_format(file, kwargs)

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
@click.option('--input-format', '-i')
@click.option('--output-format', '-o')
def schema_transcode(infile: str, outfile: str, **kwargs):
    """Transcodes schema file into another format"""
    logging.info(f'Transcoding schema from `{infile}` to `{outfile}`:')

    schema = load_shema(infile)

    logging.info('- serializing data')
    with open(outfile, 'wb') as f:
        schema.stream_serialize(f)
        pos = f.tell()
    logging.info(
        f'''Schema `{schema.name}`, version {schema.schema_ver} was transcoded into `{outfile}`; {pos} byes written,
          schema hash is {schema.bech32_id()}''')


@main.command()
@click.argument('file')
@click.option('--format', '-f')
@click.option('--schema', '-s')
def proof_validate(file: str, **kwargs) -> Schema:
    """Loads and validates internal structure for a given proof"""
    logging.info(f'Validating proof from `{file}`:')
    format = guess_format(file, kwargs)

    if 'schema' in kwargs:
        schema = load_shema(kwargs['schema'])

    logging.info(f'- loading proof data from `{file}`')
    with open(file) as f:
        data = yaml.safe_load(f)
    proof = Proof(schema_obj=schema, **data)


@main.command()
@click.argument('infile')
@click.argument('outfile')
@click.option('--schema', '-s')
@click.option('--input-format', '-i')
@click.option('--output-format', '-o')
def proof_transcode(infile: str, outfile: str, **kwargs):
    """Transcodes proof file into another format"""
    logging.info(f'Transcoding proof from `{infile}` to `{outfile}`:')

    if 'schema' in kwargs:
        schema = load_shema(kwargs['schema'])

    logging.info(f'- loading proof data from `{infile}`')
    with open(infile) as f:
        data = yaml.safe_load(f)
    proof = Proof(schema_obj=schema, **data)

    logging.info('- serializing data')
    with open(outfile, 'wb') as f:
        proof.stream_serialize(f)
        pos = f.tell()
    logging.info(
        f'''Proof `{infile}` was transcoded into `{outfile}`; {pos} byes written,
          proof hash is {proof.bech32_id()}''')


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    main()
