# -*- coding: utf-8 -*-

from binascii import unhexlify
from functools import reduce
from typing import Iterable

address_bits = {
    0: 16,
    1: 16,
    2: 24,
    3: 32,
    5: 16,
    7: 32,
    8: 24,
    9: 16
}


def make_record(rectype: int, address: int, data: bytes or None = None) -> str:
    if data is None:
        data = b""

    addr = f"{address:x}".rjust(address_bits[rectype] >> 2, "0")
    count = (len(addr) >> 1) + len(data) + 1
    rec = f"S{rectype:1d}{count:02x}{addr}{data.hex()}"
    checksum = (reduce(lambda a, b: a + b, unhexlify(rec[2:])) % 256) ^ 255
    reccs = f"{rec}{checksum:02x}\r\n"
    return reccs


def make(address_bits: int, records: Iterable, name:str, version: int = 1, revision: int = 1,
         comment: str = "thd74tool") -> Iterable[str]:
        assert address_bits in [16, 24, 32]
        assert len(comment) <= 36
        # CAVE: we do not emit count records

        # Create header record
        name = name.encode("ascii").ljust(20, b"\x00")
        version = unhexlify(f"{version:04x}")
        revision = unhexlify(f"{revision:04x}")
        comment = comment.encode("ascii")
        yield make_record(0, 0, name + version + revision + comment)

        data_type, term_type = {
            16: (1, 9),
            24: (2, 8),
            32: (3, 7)
        }[address_bits]
        for addr, data in records:
            yield make_record(data_type, addr, data)
        # CAVE: We do not know the start execution address for the termination record, defaulting to 0
        yield make_record(term_type, 0)
