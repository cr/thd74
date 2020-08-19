# -*- coding: utf-8 -*-

from binascii import hexlify, unhexlify
from functools import reduce
from logging import getLogger
from struct import pack, unpack
from time import time, sleep
from typing import List, Iterable

from . import tty as thdtty

logger = getLogger(__name__)


class ProtocolError(Exception):
    pass


class Message(object):
    """
    Generic THD Message Object
    """

    def __init__(self, verb: int = 0, nouns: Iterable[bytes] = None, payload: Iterable[bytes] = None, parse: bytes = None, key: int = 0):
        # 0xab 0xab [2 byte length] [2 byte payload length] [2 byte verb] [optional nouns] [optional payload] [1 byte checksum]
        self.verb = verb
        self.nouns = nouns or []
        self.payload = payload or []
        self.key = key or 0
        self.checksum_recv = None

        if parse is not None:
            if parse[0] == parse[1]:
                # FWPROG mode command message
                self.key = parse[0] ^ 0xab
                cl = bytes([x ^ self.key for x in parse.rstrip(b"\r\n")])
                ncl, pl, self.verb = unpack(">xxHHH", cl[:8])
                n, p, self.checksum_recv = unpack(f">8x{ncl-1}s{pl}sB", cl)
                self.nouns = [n]
                self.payload = [p]

            else:
                raise ProtocolError(f"Invalid message `{parse}`")

    def validate(self, checksum=None):
        if checksum is None:
            checksum = self.checksum
        if self.checksum_recv is None:
            return True
        return checksum == self.checksum_recv

    @property
    def checksum(self):
        return reduce(lambda x, y: x + y, self.__bytes_no_check()[2:], 0) % 256

    def __bytes_no_check(self):
        ncl = reduce(lambda x, y: x + len(y), self.nouns, 1) % 256
        pl = reduce(lambda x, y: x + len(y), self.payload, 0) % 256
        return b"\xab\xab" + pack(f">HHH{ncl-1}s{pl}s", ncl, pl, self.verb, b"".join(self.nouns), b"".join(self.payload))

    def __bytes__(self):
        msg = self.__bytes_no_check()
        msg += bytes([reduce(lambda x, y: x + y, msg[2:], 0) % 256])
        return bytes(map(lambda x: x ^ self.key, msg)) + b"\r\n"

    def __str__(self):
        msg = self.__bytes_no_check()
        msg += bytes([reduce(lambda x, y: x + y, msg[2:], 0) % 256])
        h = msg.hex()
        return " ".join([h[i:i+2] for i in range(0, len(h), 2)]) + f" [^{self.key:02x}]"

    def __repr__(self):
        return repr(bytes(self))

    def __iter__(self):
        for b in bytes(self):
            yield b

    def __eq__(self, other):
        if str(self) != str(other):
            return False
        else:
            if self.checksum_recv == other.checksum_recv:
                return True
            else:
                if self.checksum_recv is None or other.checksum_recv is None:
                    return True
                else:
                    return False

    @classmethod
    def parse(cls, messages):
        if type(messages) is bytes:
            messages = messages.decode('ascii')
        for message in messages.split("\r\n"):
            if len(message) > 0:
                yield cls(parse=message)


class GenericTHDProtocol(object):

    def __init__(self, tty=None):
        self.conn = None
        self.connected = False
        self.thd_hardware = False
        self.fwprog_mode = False
        self.pcrig_mode = False
        self.key = None
        self.__connect(tty)

    def __connect(self, tty):
        self.conn = thdtty.GenericTHDTTY(tty)
        self.__detect_device_mode()
        self.connected = True
        if self.thd_hardware:
            logger.debug("Device responds like THD style hardware")
        else:
            logger.debug("Device behaves not like THD style hardware")
        if self.pcrig_mode:
            logger.debug("Device is in PCRIG mode")
        if self.fwprog_mode:
            logger.debug("Device is in FWPROG mode")
            # logger.debug("Switching to command mode")
            # self.cmd_mode()
            # self.sync()

    def __detect_device_mode(self):
        self.conn.flush_input()
        self.conn.flush_output()

        self.conn.write(b"ID\r")
        sleep(0.5)
        try:
            r = self.conn.read_all()
        except TimeoutError:
            logger.debug("No response, so probably in FWPROG mode")
            self.thd_hardware = True
            self.pcrig_mode = False
            self.fwprog_mode = True
            return

        if r.startswith(b"ID "):
            logger.debug("Response like THD hardware in PCRIG mode")
            self.thd_hardware = True
            self.pcrig_mode = True
            self.fwprog_mode = False
            return

        logger.warning("Unknown response from `ID` command")
        self.thd_hardware = False
        self.pcrig_mode = True
        self.fwprog_mode = False
        return

    def available(self):
        return self.conn.available()

    def write(self, data):
        return self.conn.write(data)

    def read(self, *args, **kwargs):
        return self.conn.read(*args, **kwargs)

    def read_all(self, *args, **kwargs):
        return self.conn.read_all(*args, **kwargs)

    def read_line(self, *args, **kwargs):
        return self.conn.read_line(*args, **kwargs)

    def send(self, verb, nouns=None, payload=None):
        self.write(Message(verb, nouns, payload, self.key))

    def receive(self):
        while True:
            m = Message(parse=self.read_line())
            return m

    def cmd_mode(self):
        if self.fwprog_mode:
            logger.debug("Sending command mode request")
            # self.write(b"\x77\x74Thd74tw\x2e\x18")
            # self.key = 2
            self.write(b"FPROMOD")
            self.key = 0
            res = self.read(2)
            if res == b"\x16\x06":
                logger.debg("Device now ready to receive commands")
            else:
                raise ProtocolError("Unexpected response to command mode request")

    def sync(self, flush_output=False, flush_input=True):
        if flush_output:
            self.conn.flush_output()
        if flush_input:
            self.conn.flush_input()
 
    def wait_for_ready(self, timeout=1):
        timeout_time = time() + timeout
        radio_status = None
        while radio_status != "00" and time() < timeout_time:
            radio_status = "00"
        if radio_status != "00":
            raise TimeoutError("Device not ready")

    def get_firmware_version(self):
        if not self.pcrig_mode:
            return None
        self.conn.write(b"FV\r")
        try:
            r = self.read(8)
        except TimeoutError:
            logger.warning("No reply from device to firware version request")
            return None
        
        if not r.startswith(b"FV "):
            logger.warning("Ignoring strange reply from device to firmware version request.")
            self.conn.flush_input()
            return None

        return r[3:].rstrip(b"\r").decode("ascii")


class THD74Protocol(GenericTHDProtocol):
    pass