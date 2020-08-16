# -*- coding: utf-8 -*-

from binascii import unhexlify
from typing import List, Iterable, Generator

from logging import getLogger
logger = getLogger(__name__)


def z_ij(i, j):
    mj = 51*(1 - 2*(j%2))  # 51, -51, 51, -51 ...
    bj = 212 + 56*j + 10*(j>>1)
    return (mj*(i + bj)) % 256


def decrypt_line(data: str, i: int = 0) -> str:
    odd = len(data) % 2 == 1
    if odd:
        data = unhexlify("0" + data)
    else:
        data = unhexlify(data)

    # Adjust offsets. j is right-aligned
    i -= 11
    jd = 22 - len(data)

    res = []
    for j, x in zip(range(len(data)), data):
        if j%2 == 1:
            res.append((z_ij(i, j+jd) - x) % 256)
        else:
            res.append((x - z_ij(i, j+jd)) % 256)

    if odd:
        return bytes(res).hex()[1:]
    else:
        return bytes(res).hex()


def decrypt_blob(blob: Iterable[str], start_offset: int = 0, end_offset: int = 49) -> Iterable[str]:
    block_number = -1
    for line in blob:
        if len(line) == 15:  # block header line
            block_number += 1
            i = (171 * block_number + start_offset) % 256
        if len(line) == 11:  # last line in blob
            i = (171 * block_number + start_offset + end_offset) % 256
        yield decrypt_line(line, i)
        i += 1


def get_columns(offset: int, length: int, out_of: List[str], unhex=True) -> Iterable[List[str]]:
    if unhex:
        yield from map(lambda x: x[offset:offset+length][0], map(unhexlify, out_of))
    else:
        yield from map(lambda x: x[offset:offset+length], out_of)
