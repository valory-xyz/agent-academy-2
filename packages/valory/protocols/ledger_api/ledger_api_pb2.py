# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ledger_api.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x10ledger_api.proto\x12\x1c\x61\x65\x61.valory.ledger_api.v1_0_0"\xaa\x1b\n\x10LedgerApiMessage\x12V\n\x07\x62\x61lance\x18\x05 \x01(\x0b\x32\x43.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Balance_PerformativeH\x00\x12R\n\x05\x65rror\x18\x06 \x01(\x0b\x32\x41.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Error_PerformativeH\x00\x12^\n\x0bget_balance\x18\x07 \x01(\x0b\x32G.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Get_Balance_PerformativeH\x00\x12n\n\x13get_raw_transaction\x18\x08 \x01(\x0b\x32O.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Get_Raw_Transaction_PerformativeH\x00\x12Z\n\tget_state\x18\t \x01(\x0b\x32\x45.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Get_State_PerformativeH\x00\x12v\n\x17get_transaction_receipt\x18\n \x01(\x0b\x32S.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Get_Transaction_Receipt_PerformativeH\x00\x12\x66\n\x0fraw_transaction\x18\x0b \x01(\x0b\x32K.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Raw_Transaction_PerformativeH\x00\x12v\n\x17send_signed_transaction\x18\x0c \x01(\x0b\x32S.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Send_Signed_Transaction_PerformativeH\x00\x12x\n\x18send_signed_transactions\x18\r \x01(\x0b\x32T.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Send_Signed_Transactions_PerformativeH\x00\x12R\n\x05state\x18\x0e \x01(\x0b\x32\x41.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.State_PerformativeH\x00\x12l\n\x12transaction_digest\x18\x0f \x01(\x0b\x32N.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Transaction_Digest_PerformativeH\x00\x12n\n\x13transaction_digests\x18\x10 \x01(\x0b\x32O.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Transaction_Digests_PerformativeH\x00\x12n\n\x13transaction_receipt\x18\x11 \x01(\x0b\x32O.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Transaction_Receipt_PerformativeH\x00\x1a\x18\n\x06Kwargs\x12\x0e\n\x06kwargs\x18\x01 \x01(\x0c\x1a)\n\x0eRawTransaction\x12\x17\n\x0fraw_transaction\x18\x01 \x01(\x0c\x1a/\n\x11SignedTransaction\x12\x1a\n\x12signed_transaction\x18\x01 \x01(\x0c\x1a\x44\n\x12SignedTransactions\x12\x11\n\tledger_id\x18\x01 \x01(\t\x12\x1b\n\x13signed_transactions\x18\x02 \x03(\x0c\x1a\x16\n\x05State\x12\r\n\x05state\x18\x01 \x01(\x0c\x1a\x16\n\x05Terms\x12\r\n\x05terms\x18\x01 \x01(\x0c\x1a/\n\x11TransactionDigest\x12\x1a\n\x12transaction_digest\x18\x01 \x01(\x0c\x1a\x44\n\x12TransactionDigests\x12\x11\n\tledger_id\x18\x01 \x01(\t\x12\x1b\n\x13transaction_digests\x18\x02 \x03(\t\x1a\x31\n\x12TransactionReceipt\x12\x1b\n\x13transaction_receipt\x18\x01 \x01(\x0c\x1a>\n\x18Get_Balance_Performative\x12\x11\n\tledger_id\x18\x01 \x01(\t\x12\x0f\n\x07\x61\x64\x64ress\x18\x02 \x01(\t\x1ag\n Get_Raw_Transaction_Performative\x12\x43\n\x05terms\x18\x01 \x01(\x0b\x32\x34.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Terms\x1a\x84\x01\n$Send_Signed_Transaction_Performative\x12\\\n\x12signed_transaction\x18\x01 \x01(\x0b\x32@.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.SignedTransaction\x1a\xce\x01\n%Send_Signed_Transactions_Performative\x12^\n\x13signed_transactions\x18\x01 \x01(\x0b\x32\x41.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.SignedTransactions\x12\x45\n\x06kwargs\x18\x02 \x01(\x0b\x32\x35.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Kwargs\x1a\xf0\x01\n$Get_Transaction_Receipt_Performative\x12\\\n\x12transaction_digest\x18\x01 \x01(\x0b\x32@.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.TransactionDigest\x12\x15\n\rretry_timeout\x18\x02 \x01(\x05\x12\x1c\n\x14retry_timeout_is_set\x18\x03 \x01(\x08\x12\x16\n\x0eretry_attempts\x18\x04 \x01(\x05\x12\x1d\n\x15retry_attempts_is_set\x18\x05 \x01(\x08\x1a:\n\x14\x42\x61lance_Performative\x12\x11\n\tledger_id\x18\x01 \x01(\t\x12\x0f\n\x07\x62\x61lance\x18\x02 \x01(\x05\x1av\n\x1cRaw_Transaction_Performative\x12V\n\x0fraw_transaction\x18\x01 \x01(\x0b\x32=.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.RawTransaction\x1a\x7f\n\x1fTransaction_Digest_Performative\x12\\\n\x12transaction_digest\x18\x01 \x01(\x0b\x32@.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.TransactionDigest\x1a\x82\x01\n Transaction_Digests_Performative\x12^\n\x13transaction_digests\x18\x01 \x01(\x0b\x32\x41.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.TransactionDigests\x1a\x82\x01\n Transaction_Receipt_Performative\x12^\n\x13transaction_receipt\x18\x01 \x01(\x0b\x32\x41.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.TransactionReceipt\x1a\x92\x01\n\x16Get_State_Performative\x12\x11\n\tledger_id\x18\x01 \x01(\t\x12\x10\n\x08\x63\x61llable\x18\x02 \x01(\t\x12\x0c\n\x04\x61rgs\x18\x03 \x03(\t\x12\x45\n\x06kwargs\x18\x04 \x01(\x0b\x32\x35.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Kwargs\x1al\n\x12State_Performative\x12\x11\n\tledger_id\x18\x01 \x01(\t\x12\x43\n\x05state\x18\x02 \x01(\x0b\x32\x34.aea.valory.ledger_api.v1_0_0.LedgerApiMessage.State\x1an\n\x12\x45rror_Performative\x12\x0c\n\x04\x63ode\x18\x01 \x01(\x05\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x16\n\x0emessage_is_set\x18\x03 \x01(\x08\x12\x0c\n\x04\x64\x61ta\x18\x04 \x01(\x0c\x12\x13\n\x0b\x64\x61ta_is_set\x18\x05 \x01(\x08\x42\x0e\n\x0cperformativeb\x06proto3'
)


_LEDGERAPIMESSAGE = DESCRIPTOR.message_types_by_name["LedgerApiMessage"]
_LEDGERAPIMESSAGE_KWARGS = _LEDGERAPIMESSAGE.nested_types_by_name["Kwargs"]
_LEDGERAPIMESSAGE_RAWTRANSACTION = _LEDGERAPIMESSAGE.nested_types_by_name[
    "RawTransaction"
]
_LEDGERAPIMESSAGE_SIGNEDTRANSACTION = _LEDGERAPIMESSAGE.nested_types_by_name[
    "SignedTransaction"
]
_LEDGERAPIMESSAGE_SIGNEDTRANSACTIONS = _LEDGERAPIMESSAGE.nested_types_by_name[
    "SignedTransactions"
]
_LEDGERAPIMESSAGE_STATE = _LEDGERAPIMESSAGE.nested_types_by_name["State"]
_LEDGERAPIMESSAGE_TERMS = _LEDGERAPIMESSAGE.nested_types_by_name["Terms"]
_LEDGERAPIMESSAGE_TRANSACTIONDIGEST = _LEDGERAPIMESSAGE.nested_types_by_name[
    "TransactionDigest"
]
_LEDGERAPIMESSAGE_TRANSACTIONDIGESTS = _LEDGERAPIMESSAGE.nested_types_by_name[
    "TransactionDigests"
]
_LEDGERAPIMESSAGE_TRANSACTIONRECEIPT = _LEDGERAPIMESSAGE.nested_types_by_name[
    "TransactionReceipt"
]
_LEDGERAPIMESSAGE_GET_BALANCE_PERFORMATIVE = _LEDGERAPIMESSAGE.nested_types_by_name[
    "Get_Balance_Performative"
]
_LEDGERAPIMESSAGE_GET_RAW_TRANSACTION_PERFORMATIVE = (
    _LEDGERAPIMESSAGE.nested_types_by_name["Get_Raw_Transaction_Performative"]
)
_LEDGERAPIMESSAGE_SEND_SIGNED_TRANSACTION_PERFORMATIVE = (
    _LEDGERAPIMESSAGE.nested_types_by_name["Send_Signed_Transaction_Performative"]
)
_LEDGERAPIMESSAGE_SEND_SIGNED_TRANSACTIONS_PERFORMATIVE = (
    _LEDGERAPIMESSAGE.nested_types_by_name["Send_Signed_Transactions_Performative"]
)
_LEDGERAPIMESSAGE_GET_TRANSACTION_RECEIPT_PERFORMATIVE = (
    _LEDGERAPIMESSAGE.nested_types_by_name["Get_Transaction_Receipt_Performative"]
)
_LEDGERAPIMESSAGE_BALANCE_PERFORMATIVE = _LEDGERAPIMESSAGE.nested_types_by_name[
    "Balance_Performative"
]
_LEDGERAPIMESSAGE_RAW_TRANSACTION_PERFORMATIVE = _LEDGERAPIMESSAGE.nested_types_by_name[
    "Raw_Transaction_Performative"
]
_LEDGERAPIMESSAGE_TRANSACTION_DIGEST_PERFORMATIVE = (
    _LEDGERAPIMESSAGE.nested_types_by_name["Transaction_Digest_Performative"]
)
_LEDGERAPIMESSAGE_TRANSACTION_DIGESTS_PERFORMATIVE = (
    _LEDGERAPIMESSAGE.nested_types_by_name["Transaction_Digests_Performative"]
)
_LEDGERAPIMESSAGE_TRANSACTION_RECEIPT_PERFORMATIVE = (
    _LEDGERAPIMESSAGE.nested_types_by_name["Transaction_Receipt_Performative"]
)
_LEDGERAPIMESSAGE_GET_STATE_PERFORMATIVE = _LEDGERAPIMESSAGE.nested_types_by_name[
    "Get_State_Performative"
]
_LEDGERAPIMESSAGE_STATE_PERFORMATIVE = _LEDGERAPIMESSAGE.nested_types_by_name[
    "State_Performative"
]
_LEDGERAPIMESSAGE_ERROR_PERFORMATIVE = _LEDGERAPIMESSAGE.nested_types_by_name[
    "Error_Performative"
]
LedgerApiMessage = _reflection.GeneratedProtocolMessageType(
    "LedgerApiMessage",
    (_message.Message,),
    {
        "Kwargs": _reflection.GeneratedProtocolMessageType(
            "Kwargs",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_KWARGS,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Kwargs)
            },
        ),
        "RawTransaction": _reflection.GeneratedProtocolMessageType(
            "RawTransaction",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_RAWTRANSACTION,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.RawTransaction)
            },
        ),
        "SignedTransaction": _reflection.GeneratedProtocolMessageType(
            "SignedTransaction",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_SIGNEDTRANSACTION,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.SignedTransaction)
            },
        ),
        "SignedTransactions": _reflection.GeneratedProtocolMessageType(
            "SignedTransactions",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_SIGNEDTRANSACTIONS,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.SignedTransactions)
            },
        ),
        "State": _reflection.GeneratedProtocolMessageType(
            "State",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_STATE,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.State)
            },
        ),
        "Terms": _reflection.GeneratedProtocolMessageType(
            "Terms",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_TERMS,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Terms)
            },
        ),
        "TransactionDigest": _reflection.GeneratedProtocolMessageType(
            "TransactionDigest",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_TRANSACTIONDIGEST,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.TransactionDigest)
            },
        ),
        "TransactionDigests": _reflection.GeneratedProtocolMessageType(
            "TransactionDigests",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_TRANSACTIONDIGESTS,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.TransactionDigests)
            },
        ),
        "TransactionReceipt": _reflection.GeneratedProtocolMessageType(
            "TransactionReceipt",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_TRANSACTIONRECEIPT,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.TransactionReceipt)
            },
        ),
        "Get_Balance_Performative": _reflection.GeneratedProtocolMessageType(
            "Get_Balance_Performative",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_GET_BALANCE_PERFORMATIVE,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Get_Balance_Performative)
            },
        ),
        "Get_Raw_Transaction_Performative": _reflection.GeneratedProtocolMessageType(
            "Get_Raw_Transaction_Performative",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_GET_RAW_TRANSACTION_PERFORMATIVE,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Get_Raw_Transaction_Performative)
            },
        ),
        "Send_Signed_Transaction_Performative": _reflection.GeneratedProtocolMessageType(
            "Send_Signed_Transaction_Performative",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_SEND_SIGNED_TRANSACTION_PERFORMATIVE,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Send_Signed_Transaction_Performative)
            },
        ),
        "Send_Signed_Transactions_Performative": _reflection.GeneratedProtocolMessageType(
            "Send_Signed_Transactions_Performative",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_SEND_SIGNED_TRANSACTIONS_PERFORMATIVE,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Send_Signed_Transactions_Performative)
            },
        ),
        "Get_Transaction_Receipt_Performative": _reflection.GeneratedProtocolMessageType(
            "Get_Transaction_Receipt_Performative",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_GET_TRANSACTION_RECEIPT_PERFORMATIVE,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Get_Transaction_Receipt_Performative)
            },
        ),
        "Balance_Performative": _reflection.GeneratedProtocolMessageType(
            "Balance_Performative",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_BALANCE_PERFORMATIVE,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Balance_Performative)
            },
        ),
        "Raw_Transaction_Performative": _reflection.GeneratedProtocolMessageType(
            "Raw_Transaction_Performative",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_RAW_TRANSACTION_PERFORMATIVE,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Raw_Transaction_Performative)
            },
        ),
        "Transaction_Digest_Performative": _reflection.GeneratedProtocolMessageType(
            "Transaction_Digest_Performative",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_TRANSACTION_DIGEST_PERFORMATIVE,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Transaction_Digest_Performative)
            },
        ),
        "Transaction_Digests_Performative": _reflection.GeneratedProtocolMessageType(
            "Transaction_Digests_Performative",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_TRANSACTION_DIGESTS_PERFORMATIVE,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Transaction_Digests_Performative)
            },
        ),
        "Transaction_Receipt_Performative": _reflection.GeneratedProtocolMessageType(
            "Transaction_Receipt_Performative",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_TRANSACTION_RECEIPT_PERFORMATIVE,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Transaction_Receipt_Performative)
            },
        ),
        "Get_State_Performative": _reflection.GeneratedProtocolMessageType(
            "Get_State_Performative",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_GET_STATE_PERFORMATIVE,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Get_State_Performative)
            },
        ),
        "State_Performative": _reflection.GeneratedProtocolMessageType(
            "State_Performative",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_STATE_PERFORMATIVE,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.State_Performative)
            },
        ),
        "Error_Performative": _reflection.GeneratedProtocolMessageType(
            "Error_Performative",
            (_message.Message,),
            {
                "DESCRIPTOR": _LEDGERAPIMESSAGE_ERROR_PERFORMATIVE,
                "__module__": "ledger_api_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage.Error_Performative)
            },
        ),
        "DESCRIPTOR": _LEDGERAPIMESSAGE,
        "__module__": "ledger_api_pb2"
        # @@protoc_insertion_point(class_scope:aea.valory.ledger_api.v1_0_0.LedgerApiMessage)
    },
)
_sym_db.RegisterMessage(LedgerApiMessage)
_sym_db.RegisterMessage(LedgerApiMessage.Kwargs)
_sym_db.RegisterMessage(LedgerApiMessage.RawTransaction)
_sym_db.RegisterMessage(LedgerApiMessage.SignedTransaction)
_sym_db.RegisterMessage(LedgerApiMessage.SignedTransactions)
_sym_db.RegisterMessage(LedgerApiMessage.State)
_sym_db.RegisterMessage(LedgerApiMessage.Terms)
_sym_db.RegisterMessage(LedgerApiMessage.TransactionDigest)
_sym_db.RegisterMessage(LedgerApiMessage.TransactionDigests)
_sym_db.RegisterMessage(LedgerApiMessage.TransactionReceipt)
_sym_db.RegisterMessage(LedgerApiMessage.Get_Balance_Performative)
_sym_db.RegisterMessage(LedgerApiMessage.Get_Raw_Transaction_Performative)
_sym_db.RegisterMessage(LedgerApiMessage.Send_Signed_Transaction_Performative)
_sym_db.RegisterMessage(LedgerApiMessage.Send_Signed_Transactions_Performative)
_sym_db.RegisterMessage(LedgerApiMessage.Get_Transaction_Receipt_Performative)
_sym_db.RegisterMessage(LedgerApiMessage.Balance_Performative)
_sym_db.RegisterMessage(LedgerApiMessage.Raw_Transaction_Performative)
_sym_db.RegisterMessage(LedgerApiMessage.Transaction_Digest_Performative)
_sym_db.RegisterMessage(LedgerApiMessage.Transaction_Digests_Performative)
_sym_db.RegisterMessage(LedgerApiMessage.Transaction_Receipt_Performative)
_sym_db.RegisterMessage(LedgerApiMessage.Get_State_Performative)
_sym_db.RegisterMessage(LedgerApiMessage.State_Performative)
_sym_db.RegisterMessage(LedgerApiMessage.Error_Performative)

if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    _LEDGERAPIMESSAGE._serialized_start = 51
    _LEDGERAPIMESSAGE._serialized_end = 3549
    _LEDGERAPIMESSAGE_KWARGS._serialized_start = 1427
    _LEDGERAPIMESSAGE_KWARGS._serialized_end = 1451
    _LEDGERAPIMESSAGE_RAWTRANSACTION._serialized_start = 1453
    _LEDGERAPIMESSAGE_RAWTRANSACTION._serialized_end = 1494
    _LEDGERAPIMESSAGE_SIGNEDTRANSACTION._serialized_start = 1496
    _LEDGERAPIMESSAGE_SIGNEDTRANSACTION._serialized_end = 1543
    _LEDGERAPIMESSAGE_SIGNEDTRANSACTIONS._serialized_start = 1545
    _LEDGERAPIMESSAGE_SIGNEDTRANSACTIONS._serialized_end = 1613
    _LEDGERAPIMESSAGE_STATE._serialized_start = 1615
    _LEDGERAPIMESSAGE_STATE._serialized_end = 1637
    _LEDGERAPIMESSAGE_TERMS._serialized_start = 1639
    _LEDGERAPIMESSAGE_TERMS._serialized_end = 1661
    _LEDGERAPIMESSAGE_TRANSACTIONDIGEST._serialized_start = 1663
    _LEDGERAPIMESSAGE_TRANSACTIONDIGEST._serialized_end = 1710
    _LEDGERAPIMESSAGE_TRANSACTIONDIGESTS._serialized_start = 1712
    _LEDGERAPIMESSAGE_TRANSACTIONDIGESTS._serialized_end = 1780
    _LEDGERAPIMESSAGE_TRANSACTIONRECEIPT._serialized_start = 1782
    _LEDGERAPIMESSAGE_TRANSACTIONRECEIPT._serialized_end = 1831
    _LEDGERAPIMESSAGE_GET_BALANCE_PERFORMATIVE._serialized_start = 1833
    _LEDGERAPIMESSAGE_GET_BALANCE_PERFORMATIVE._serialized_end = 1895
    _LEDGERAPIMESSAGE_GET_RAW_TRANSACTION_PERFORMATIVE._serialized_start = 1897
    _LEDGERAPIMESSAGE_GET_RAW_TRANSACTION_PERFORMATIVE._serialized_end = 2000
    _LEDGERAPIMESSAGE_SEND_SIGNED_TRANSACTION_PERFORMATIVE._serialized_start = 2003
    _LEDGERAPIMESSAGE_SEND_SIGNED_TRANSACTION_PERFORMATIVE._serialized_end = 2135
    _LEDGERAPIMESSAGE_SEND_SIGNED_TRANSACTIONS_PERFORMATIVE._serialized_start = 2138
    _LEDGERAPIMESSAGE_SEND_SIGNED_TRANSACTIONS_PERFORMATIVE._serialized_end = 2344
    _LEDGERAPIMESSAGE_GET_TRANSACTION_RECEIPT_PERFORMATIVE._serialized_start = 2347
    _LEDGERAPIMESSAGE_GET_TRANSACTION_RECEIPT_PERFORMATIVE._serialized_end = 2587
    _LEDGERAPIMESSAGE_BALANCE_PERFORMATIVE._serialized_start = 2589
    _LEDGERAPIMESSAGE_BALANCE_PERFORMATIVE._serialized_end = 2647
    _LEDGERAPIMESSAGE_RAW_TRANSACTION_PERFORMATIVE._serialized_start = 2649
    _LEDGERAPIMESSAGE_RAW_TRANSACTION_PERFORMATIVE._serialized_end = 2767
    _LEDGERAPIMESSAGE_TRANSACTION_DIGEST_PERFORMATIVE._serialized_start = 2769
    _LEDGERAPIMESSAGE_TRANSACTION_DIGEST_PERFORMATIVE._serialized_end = 2896
    _LEDGERAPIMESSAGE_TRANSACTION_DIGESTS_PERFORMATIVE._serialized_start = 2899
    _LEDGERAPIMESSAGE_TRANSACTION_DIGESTS_PERFORMATIVE._serialized_end = 3029
    _LEDGERAPIMESSAGE_TRANSACTION_RECEIPT_PERFORMATIVE._serialized_start = 3032
    _LEDGERAPIMESSAGE_TRANSACTION_RECEIPT_PERFORMATIVE._serialized_end = 3162
    _LEDGERAPIMESSAGE_GET_STATE_PERFORMATIVE._serialized_start = 3165
    _LEDGERAPIMESSAGE_GET_STATE_PERFORMATIVE._serialized_end = 3311
    _LEDGERAPIMESSAGE_STATE_PERFORMATIVE._serialized_start = 3313
    _LEDGERAPIMESSAGE_STATE_PERFORMATIVE._serialized_end = 3421
    _LEDGERAPIMESSAGE_ERROR_PERFORMATIVE._serialized_start = 3423
    _LEDGERAPIMESSAGE_ERROR_PERFORMATIVE._serialized_end = 3533
# @@protoc_insertion_point(module_scope)
