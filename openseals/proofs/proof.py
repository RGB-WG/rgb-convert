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

from io import BytesIO
from enum import unique
from functools import reduce

from bitcoin.core.serialize import Serializable, ImmutableSerializable, \
                                   VectorSerializer, VarIntSerializer, BytesSerializer, ser_read
import bitcoin.segwit_addr as bech32

from openseals.consensus import *
from openseals.data_types import Hash256Id, PubKey, Network, OutPoint
from openseals.parser import *
from openseals.proofs.meta_field import MetaField
from openseals.proofs.seal import Seal
from openseals.schema.schema import Schema, SchemaError


@unique
class ProofFormat(FieldEnum):
    root = 0x00
    upgrade = 0x01
    ordinary = 0x02
    burn = 0x03


class Proof(ImmutableSerializable):

    FIELDS = {
        'ver': FieldParser(int, required=False),
        'format': FieldParser(ProofFormat, required=False, default=ProofFormat.ordinary),
        'schema': FieldParser(Hash256Id, required=False),
        'network': FieldParser(Network, required=False),
        'root': FieldParser(OutPoint, required=False),
        'type_name': FieldParser(str, required=True),
        'fields': FieldParser(MetaField, required=False, array=True),
        'seals': FieldParser(Seal, required=False, array=True),
        'pubkey': FieldParser(PubKey, required=False),
        'parents': FieldParser(Hash256Id, required=False, array=True),
        'txid': FieldParser(Hash256Id, required=False)
    }

    __slots__ = list(FIELDS.keys()) + ['schema_obj', 'state', 'metadata', 'type_no', 'proof_type']

    def __init__(self, type_no=None, schema_obj=None, **kwargs):
        if 'format' in kwargs and isinstance(kwargs['format'], ProofFormat):
            if type_no is None:
                raise AttributeError('constructing proof requires providing type id')
            object.__setattr__(self, 'type_no', type_no)
            object.__setattr__(self, 'type_name', None)
            object.__setattr__(self, 'fields', None)
            object.__setattr__(self, 'state', None)
            object.__setattr__(self, 'metadata', None)
            [object.__setattr__(self, attr, value) for attr, value in kwargs.items()]
            object.__setattr__(self, 'schema_obj', schema_obj)
            return

        for name, field in Proof.FIELDS.items():
            field.parse(self, kwargs, name)

        for field in ['ver', 'schema', 'network', 'root']:
            val = object.__getattribute__(self, field)
            if val is None and self.format is ProofFormat.root:
                raise FieldParseError(FieldParseError.Kind.noRequiredField,
                                      field, 'field must be present the root proof')
            elif val is not None:
                if self.format is ProofFormat.upgrade and field in ['ver', 'schema']:
                    pass
                elif self.format is not ProofFormat.root:
                    raise FieldParseError(FieldParseError.Kind.extraField,
                                          field, 'field must be present in root proof only')
        if (self.parents is not None and self.txid is None) or (self.parents is None and self.txid is not None):
            raise FieldParseError(FieldParseError.Kind.noRequiredField,
                                  'parents' if self.parents is None else 'txid',
                                  'both `parents` and `txid` fields must be present for non-pruned proof data')

        object.__setattr__(self, 'type_no', None)
        object.__setattr__(self, 'state', None)
        object.__setattr__(self, 'metadata', None)

        if isinstance(schema_obj, Schema):
            self.resolve_schema(schema_obj)

    def resolve_schema(self, schema: Schema):
        object.__setattr__(self, 'schema_obj', schema)
        if not isinstance(schema, Schema):
            raise ValueError(f'`schema` parameter must be of Schema type; got `{schema}` instead')

        self.resolve_schema_refs(schema.proof_types)
        if self.proof_type is None:
            raise SchemaError(f'the provided schema `{schema.name}` does not define proof type `{self.type_name}` '
                              f'or type with index number {self.type_no}')

        [seal.resolve_schema(schema) for seal in self.seals]
        if self.fields is not None:
            [field.resolve_schema(schema) for field in self.fields]
        else:
            object.__setattr__(self, 'fields', [])

        fields = []
        for field_ref in self.proof_type.fields:
            field = field_ref.type
            try:
                pos = next(num for num, f in enumerate(self.fields) if f.type_name == field.name)
                fields.append(self.fields[pos])
            except:
                fields.append(MetaField(type_name=field.name, value=None, schema_obj=schema))
        object.__setattr__(self, 'fields', fields)

        if self.state is not None:
            self._parse_data_with_schema()

    def resolve_schema_refs(self, proof_types: list):
        try:
            proof_type = proof_types[self.type_no]
            object.__setattr__(self, 'type_name', proof_type.name)
        except:
            try:
                pos = next(num for num, type in enumerate(proof_types) if type.name == self.type_name)
                proof_type = proof_types[pos]
                object.__setattr__(self, 'type_no', pos)
            except StopIteration:
                proof_type = None

        object.__setattr__(self, 'proof_type', proof_type)

    def _parse_data_with_schema(self):
        [seal.resolve_schema(self.schema_obj) for seal in self.seals]

        pos = 0
        for seal in self.seals:
            pos = seal.parse_state_from_blob(self.state, pos)

        f = BytesIO(self.metadata)
        fields = []
        field_no = 0
        for field_ref in self.proof_type.fields:
            value = field_ref.stream_deserialize_value(f)
            field = MetaField(type_name=field_ref.type.name, value=value, schema_obj=self.schema_obj)
            fields.append(field)
            field_no += 1

        object.__setattr__(self, 'fields', fields)

        left = f.read()
        if len(left) != 0:
            raise SchemaError(f'Not all metadata bytes were consumed during deserialization, {left} bytes left')

    def validate(self):
        # TODO: check format compliance
        pass

    def bech32_id(self) -> str:
        return bech32.encode('pf', 1, self.GetHash())

    def structure_serialize(self, **kwargs) -> dict:
        data = {}
        for field_name in Proof.FIELDS.keys():
            value = self.__getattribute__(field_name)
            if isinstance(value, list):
                value = [item.structure_serialize(**kwargs) for item in value]
            elif issubclass(type(value), StructureSerializable) or issubclass(type(value), FieldEnum):
                value = value.structure_serialize(**kwargs)
            data[field_name] = value

        if 'schema' in data:
            data['schema'] = self.schema.structure_serialize(bech32=True, **kwargs)

        fields = {}
        for field in data['fields']:
            for name, value in field.items():
                if value is not None:
                    fields[name] = value
        data['fields'] = fields

        return data

    @classmethod
    def stream_deserialize(cls, f, **kwargs):
        schema_obj = kwargs['schema_obj'] if 'schema_obj' in kwargs else None
        if not isinstance(schema_obj, Schema):
            raise ValueError(f'`schema_obj` parameter must be of Schema type; got `{schema_obj}` instead')

        # Deserialize proof header
        # - version with flag
        (ver, flag) = FlagVarIntSerializer.stream_deserialize(f)
        # - fields common for root and upgrade proofs
        if flag:
            schema = Hash256Id.stream_deserialize(f)
            network = VarIntSerializer.stream_deserialize(f)
            if network is 0x00:
                format = ProofFormat.upgrade
            # - root-specific fields
            else:
                network = Network(network)
                format = ProofFormat.root
                root = OutPoint.stream_deserialize(f, short=False)
        else:
            format = ProofFormat.ordinary

        # Deserialize proof body
        # - reading proof type
        type_no = ser_read(f, 1)[0]

        # - reading `seal_sequence` structure
        seals = []
        seal_type_no = 0
        # -- we iterate over the seals until 0xFF (=FlagVarIntSerializer.Separator.EOF) byte is met
        while True:
            try:
                # -- reading seal with the current type number
                seal = Seal.stream_deserialize(f, type_no=seal_type_no, schema_obj=schema_obj)
            except BaseException as ex:
                # due to some strange but python 3 is unable to capture SeparatorByteSignal exception by its type,
                # and `isinstance(ex, SeparatorByteSignal)` returns False as well :(
                # so we have to capture generic exception and re-raise if it is not SeparatorByteSignal, which
                # can be determined only by the presence of its method
                if not callable(getattr(ex, "is_eol", None)):
                    raise
                if ex.is_eol():
                    # -- met 0xFE separator byte, increasing current type number
                    seal_type_no = seal_type_no + 1
                elif ex.is_eof():
                    # -- end of `seal_sequence` structure
                    break
            else:
                # -- otherwise append read seal to the list of seals
                seals.append(seal)

        # -- if we had zero seals implies proof of state destruction format
        if len(seals) is 0:
            format = ProofFormat.burn

        # - reading unparsed state and metadata bytes
        state = BytesSerializer.stream_deserialize(f)
        metadata = BytesSerializer.stream_deserialize(f)

        # Deserialize original public key
        pkcode = ser_read(f, 1)
        if pkcode is 0x00:
            pubkey = None
        else:
            buf = pkcode + ser_read(f, 32)
            pubkey = PubKey.deserialize(buf)

        # Deserialize prunable data
        try:
            pruned_flag = ser_read(f, 1)
        except:
            pruned_flag = 0x00

        txid, parents = None, None
        if pruned_flag & 0x01 > 0:
            txid = Hash256Id.stream_deserialize(f)
        if pruned_flag & 0x02 > 0:
            parents = VectorSerializer.stream_deserialize(Hash256Id, f)

        proof = Proof(
            schema_obj=schema_obj, type_no=type_no,
            ver=ver, format=format, schema=schema, network=network, root=root, pubkey=pubkey,
            fields=None, seals=seals, txid=txid, parents=parents, metadata=metadata, state=state
        )

        # Parsing raw seals and metadata and resolving types against the provided Schema
        if 'schema_obj' in kwargs:
            schema_obj = kwargs['schema_obj']
        if isinstance(schema_obj, Schema):
            proof.resolve_schema(schema_obj)

        return proof

    def stream_serialize(self, f, **kwargs):
        # Serialize proof header
        # - version with flag
        ver = self.ver if self.ver is not None else 0
        flag = self.format is ProofFormat.root or self.format is ProofFormat.upgrade
        FlagVarIntSerializer.stream_serialize((ver, flag), f)
        # - root proof fields
        if self.format is ProofFormat.root:
            self.schema.stream_serialize(f)
            VarIntSerializer.stream_serialize(self.network.value, f)
            self.root.stream_serialize(f, short_form=False)
        # - version upgrade proof fields
        elif self.format is ProofFormat.upgrade:
            if self.schema is not None:
                self.schema.stream_serialize(f)
            else:
                ZeroBytesSerializer.stream_serialize(32, f)
            ZeroBytesSerializer.stream_serialize(1, f)

        # Serialize proof body
        # - serializing proof type
        if self.type_no is None:
            raise ValueError('proof consensus serialization requires `type_no` to be known')
        f.write(bytes([self.type_no]))

        # - writing `seal_sequence` structure
        current_type_no = None
        for seal in self.seals:
            if current_type_no is None:
                current_type_no = seal.type_no
            elif seal.type_no is not current_type_no:
                # -- writing EOL byte to signify the change of the type
                [f.write(bytes([0x7F])) for n in range(current_type_no, seal.type_no)]
                current_type_no = seal.type_no
            seal.stream_serialize(f, state=False)
        f.write(bytes([0xFF]))

        # - writing raw data for the sealed state
        length = reduce((lambda acc, seal: acc + len(seal.serialize({'state': True}))), [0] + self.seals)
        VarIntSerializer.stream_serialize(length, f)
        [seal.stream_serialize(f, state=True) for seal in self.seals]

        # - writing raw data for all metafields
        length = reduce((lambda acc, field: acc + len(field.serialize())), [0] + self.fields)
        VarIntSerializer.stream_serialize(length, f)
        [field.stream_serialize(f) for field in self.fields]

        # Serialize original public key
        if self.pubkey is not None:
            self.pubkey.stream_serialize(f)
        else:
            ZeroBytesSerializer.stream_serialize(1, f)

        # Serialize prunable data
        if self.txid is not None:
            if self.parents is not None:
                f.write(bytes(0x03))
                self.txid.stream_serialize(f)
            else:
                f.write(bytes(0x01))
            VectorSerializer.stream_serialize(Hash256Id, self.parents, f)
        elif self.parents is not None:
            f.write(bytes(0x02))
            VectorSerializer.stream_serialize(Hash256Id, self.parents, f)
        else:
            f.write(bytes(0x00))
