# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: agent.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'agent.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0b\x61gent.proto\x12\x15prompits.plugs.protos\"\x07\n\x05\x45mpty\"G\n\x07Message\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04type\x18\x02 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x03 \x01(\t\x12\x11\n\ttimestamp\x18\x04 \x01(\x03\"3\n\x0fMessageResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"\\\n\tAgentInfo\x12\x10\n\x08\x61gent_id\x18\x01 \x01(\t\x12\x12\n\nagent_name\x18\x02 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x03 \x01(\t\x12\x14\n\x0c\x63\x61pabilities\x18\x04 \x03(\t\"B\n\x0cPracticeList\x12\x32\n\tpractices\x18\x01 \x03(\x0b\x32\x1f.prompits.plugs.protos.Practice\"c\n\x08Practice\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x02 \x01(\t\x12\x34\n\nparameters\x18\x03 \x03(\x0b\x32 .prompits.plugs.protos.Parameter\"P\n\tParameter\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04type\x18\x02 \x01(\t\x12\x10\n\x08required\x18\x03 \x01(\x08\x12\x15\n\rdefault_value\x18\x04 \x01(\t\"\xa7\x01\n\x0fPracticeRequest\x12\x15\n\rpractice_name\x18\x01 \x01(\t\x12J\n\nparameters\x18\x02 \x03(\x0b\x32\x36.prompits.plugs.protos.PracticeRequest.ParametersEntry\x1a\x31\n\x0fParametersEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"B\n\x10PracticeResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0e\n\x06result\x18\x02 \x01(\t\x12\r\n\x05\x65rror\x18\x03 \x01(\t2\xb8\x03\n\x05\x41gent\x12W\n\x0bSendMessage\x12\x1e.prompits.plugs.protos.Message\x1a&.prompits.plugs.protos.MessageResponse\"\x00\x12H\n\x04\x45\x63ho\x12\x1e.prompits.plugs.protos.Message\x1a\x1e.prompits.plugs.protos.Message\"\x00\x12P\n\x0cGetAgentInfo\x12\x1c.prompits.plugs.protos.Empty\x1a .prompits.plugs.protos.AgentInfo\"\x00\x12T\n\rListPractices\x12\x1c.prompits.plugs.protos.Empty\x1a#.prompits.plugs.protos.PracticeList\"\x00\x12\x64\n\x0f\x45xecutePractice\x12&.prompits.plugs.protos.PracticeRequest\x1a\'.prompits.plugs.protos.PracticeResponse\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'agent_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_PRACTICEREQUEST_PARAMETERSENTRY']._loaded_options = None
  _globals['_PRACTICEREQUEST_PARAMETERSENTRY']._serialized_options = b'8\001'
  _globals['_EMPTY']._serialized_start=38
  _globals['_EMPTY']._serialized_end=45
  _globals['_MESSAGE']._serialized_start=47
  _globals['_MESSAGE']._serialized_end=118
  _globals['_MESSAGERESPONSE']._serialized_start=120
  _globals['_MESSAGERESPONSE']._serialized_end=171
  _globals['_AGENTINFO']._serialized_start=173
  _globals['_AGENTINFO']._serialized_end=265
  _globals['_PRACTICELIST']._serialized_start=267
  _globals['_PRACTICELIST']._serialized_end=333
  _globals['_PRACTICE']._serialized_start=335
  _globals['_PRACTICE']._serialized_end=434
  _globals['_PARAMETER']._serialized_start=436
  _globals['_PARAMETER']._serialized_end=516
  _globals['_PRACTICEREQUEST']._serialized_start=519
  _globals['_PRACTICEREQUEST']._serialized_end=686
  _globals['_PRACTICEREQUEST_PARAMETERSENTRY']._serialized_start=637
  _globals['_PRACTICEREQUEST_PARAMETERSENTRY']._serialized_end=686
  _globals['_PRACTICERESPONSE']._serialized_start=688
  _globals['_PRACTICERESPONSE']._serialized_end=754
  _globals['_AGENT']._serialized_start=757
  _globals['_AGENT']._serialized_end=1197
# @@protoc_insertion_point(module_scope)
