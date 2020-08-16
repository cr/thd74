# -*- coding: utf-8 -*-

import json
from typing import Tuple, Generator, Iterable

from logging import getLogger
logger = getLogger(__name__)


def extract_from_json(s: str) -> Generator[int, int, bytes]:
    for pkt in json.loads(s):
        l = pkt["_source"]["layers"]
        if not "usb" in l["frame"]["frame.protocols"]:
            continue
        nr = int(l["frame"]["frame.number"])
        if int(l["usb"]["usb.transfer_type"], 16) != 3:
            continue
        if not "usb.capdata" in l:
            continue
        msg = bytes(map(lambda x: int(x, 16), l["usb.capdata"].split(":")))
        direction = int(l["usb"]["usb.endpoint_address_tree"]["usb.endpoint_address.direction"])
        yield nr, direction, msg

key = 0

def deobfuscate(data: Iterable[Tuple[int, int, bytes]]):
    global key
    for nr, direction, msg in data:
        if len(msg) > 2 and msg[0] == msg[1]:
            key = msg[0] ^ 0xab
            yield nr, direction, bytes(map(lambda x: x^key, msg))
        else:
            yield nr, direction, msg
