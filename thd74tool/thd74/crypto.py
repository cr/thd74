# -*- coding: utf-8 -*-

from binascii import unhexlify
from typing import List, Iterable, Generator

from logging import getLogger
logger = getLogger(__name__)

def permute(m: int, b: int, x: int) -> int:
     return (m*x+b)%256

def mk(n: int) -> (int, int):
    return 5-10*(n%2), ((n*61-5*(n%2))+47)%256

IV = '0026B27464C21610C85E7AAC2CFADE48'

def decrypt_updater_firmware(hexdata) -> bytes:
    global IV
    iv = unhexlify(IV)
    return b"".join(decrypt(iv, 5, map(unhexlify, hexdata)))


def decrypt_old(iv, offset, data: Iterable[bytes], even=True) -> Iterable[bytes]:
    n = -5
    decoded = []
    for dat in data:
        assert len(iv) == len(dat)
        decr = b""
        for p in range(len(dat)):
            x = dat[p]
            s = 1 if p%2==0 else -1  # interlaced permutation
            if not even:
                s = -s
            dcr = (-(permute(5, -s*5*iv[p], s*(x))-n+offset))%256
            dcrz = (permute(205, 0, dcr) - 1)%256  # final uniform rotation
            decr += bytes([dcrz])
        decoded.append(decr)
    return decoded


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


def decrypt(data: Iterable[bytes], line_offset=0, byte_offset=0) -> Iterable[bytes]:
    decoded = []
    n = line_offset
    for dat in data:
        decr = b""
        l = len(dat)
        for p in range(l):
            x = dat[p]
            m, k = mk(l - p - byte_offset)
            print(n, l, x, m, k)
            dcr = (permute(m, k, x - n) - 1)%256
            decr += bytes([dcr])
        decoded.append(decr)
        n += 1
    return decoded


def z_ij(i, j):
    mj = 51*(1 - 2*(j%2))  # 51, -51, 51, -51 ...
    bj = 212 + 56*j + 10*(j>>1)
    return (mj*(i + bj)) % 256


def get_columns(offset: int, length: int, out_of: List[str], unhex=True) -> Iterable[List[str]]:
    if unhex:
        yield from map(lambda x: x[offset:offset+length][0], map(unhexlify, out_of))
    else:
        yield from map(lambda x: x[offset:offset+length], out_of)


# find_zeros(data)