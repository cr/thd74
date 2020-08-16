# -*- coding: utf-8 -*-

from binascii import unhexlify
from functools import reduce
import sys
from struct import unpack
from typing import List, Iterable, Generator, Tuple

from .crypto import decrypt_line

from logging import getLogger
logger = getLogger(__name__)


sections = [
    {
        "name": "FIRMWARE",
        "typical_length": 2621440,
        "permute_offset": 0,
        "end_offset": 49,
        "marker_data": b"Firmware",
        "marker_offset": 0x88,
        "version_offset": 0xa0,
        "version_length": 9,
        "memory_address": 0x00200000
    },
    {
        "name": "IMAGE DATA",
        "typical_length": 393216,
        "permute_offset": 233,
        "end_offset": 49,
        "marker_data": b"1.00.",
        "marker_offset": 0,
        "version_offset": 0,
        "version_length": 10,
        "memory_address": 0x00600000
    },
    {
        "name": "DATA 00E0",
        "typical_length": 1048576,
        "permute_offset": 52,
        "end_offset": 49,
        "marker_data": b"\x5a\xa3\x00\x00\xa2\x03\x00\x02",
        "marker_offset": 0,
        "version_offset": None,
        "version_length": 0,
        "memory_address": 0x00e00000
    },
    {
        "name": "DATA 0100",
        "typical_length": 2097152,
        "permute_offset": 191,
        "end_offset": 49,
        "marker_data": b"\xae\x00\x00\x00\x30\x07\x00",
        "marker_offset": 0,
        "version_offset": None,
        "version_length": 0,
        "memory_address": 0x01000000
    },
    {
        "name": "FONT DATA",
        "typical_length": 786432,
        "permute_offset": 79,
        "end_offset": 49,
        "marker_data": b"FONT DATA",
        "marker_offset": 5,
        "version_offset": 0x10,
        "version_length": 6,
        "memory_address": 0x01500000
    },
    {
        "name": "CHECKBYTES",
        "typical_length": 2,
        "permute_offset": 9,
        "end_offset": 49,
        "marker_data": b"\xcd\xb6",
        "marker_offset": 0,
        "version_offset": None,
        "version_length": 0,
        "memory_address": 0x00200062
    },
    {
        "name": "FINAL ZZZ",
        "typical_length": 32,
        "permute_offset": 131,
        "end_offset": 51,
        "marker_data": b"ZZzo..",
        "marker_offset": 0,
        "version_offset": 0x15,
        "version_length": 10,
        "memory_address": 0x00200040
    }
]


def extract_from_exe(exe: bytes) -> List[str] or None:
    try:
        offset = exe.index(b"TH-D74 Firmware Updater") + 24
    except ValueError:
        return None

    length = unpack("<L", exe[offset:offset+4])[0]
    start = offset + 4
    end = start + length

    return exe[start:end].decode("ascii").split()


def get_flash_blobs(data: Iterable[str]) -> Iterable[List[str]]:
    blob = []
    for line in data:
        if line.startswith("$"):
            continue
        if len(line) == 15 and (len(blob) % 4097) == 0:  # block header
            blob.append(line)
        elif len(line) == 11:  # blob end record
            blob.append(line)
            yield blob
            blob = []
        else:
            blob.append(line)


# def get_data_lines(data: Iterable[str], as_bytes = False) -> Iterable[List[str]]:
#     for line in data:
#         if not line.startswith("$") and len(line) != 15 and len(line) != 11:
#             if not as_bytes:
#                 yield line
#             else:
#                 yield unhexlify(line)


def identify_blob(blob: List[str], blob_number) -> dict or None:
    # TODO: atm we detect sections exclusively by permute offset
    if len(blob[0]) != 15 or len(blob[-1]) != 11:
        logger.debug(f"Unexpected blob format for blob [{blob_number}]")
        return None
    # Try to ID by permute offset
    permute_offsets = [s["permute_offset"] for s in sections]
    for permute_offset in permute_offsets:
        test_line = decrypt_line(blob[0], permute_offset)
        if "020000040000" in test_line:
            return sections[permute_offsets.index(permute_offset)].copy()
    return None


def count_blob_bytes(blob: List[str]) -> int:
    size = 0
    for n, line in zip(range(len(blob) - 1), blob):
        if len(line) == 15 and (n % 4097) == 0:
            continue  # likely header line
        size += (len(line) - 11) >> 1
    return size


def parse_blob_line(line: str, verify=True) -> dict:
    payload_length = int(line[1:3], 16)
    r = {
        "unknown_padding": line[0],
        "payload_length": payload_length,
        "noun": int(line[3:7], 16),
        "verb": int(line[7:9], 16),
        "payload": unhexlify(line[9:9 + 2 * payload_length]),
        "checksum": int(line[-2:], 16)
    }
    if verify and not verify_record(r):
        raise Exception("parse_data_line: checksum error")  # TODO: proper exception
    return r


def record_checksum(r: dict) -> int:
    check = r["payload_length"]
    check += r["noun"] >> 8
    check += r["noun"] & 255
    check += r["verb"]
    check += reduce(lambda a, b: a + b, r["payload"], 0)
    check += r["checksum"]
    return check % 256


def verify_record(r: dict) -> bool:
    return record_checksum(r) == 0


def parse_blob(blob: Iterable[str], start_address: int = 0) -> Iterable[Tuple]:
    block_address = start_address
    for record in map(parse_blob_line, blob):
        if record["verb"] == 4:  # new block
            logger.debug(f"""New block at {int(record["payload"].hex(), 16) * 65536 + start_address:08x}""")
            block_address = int(record["payload"].hex(), 16) * 65536 + start_address
        elif record["verb"] == 0:  # data record
            yield (block_address + record["noun"], record["payload"])
        elif record["verb"] == 1:  # end of blob
            return  # TODO: check sanity, all lines consumed
        else:
            raise Exception("parse_blob: unknown record type")  # TODO: proper exception
