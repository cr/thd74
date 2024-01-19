# -*- coding: utf-8 -*-

from binascii import hexlify
from logging import getLogger
from pathlib import Path
from struct import unpack

from .base import CliCommand
from ..thd74.pcap import extract_from_json, deobfuscate

logger = getLogger(__name__)


class PcapCommand(CliCommand):

    name = "pcap"
    help = "dump flasher packets from pcap files"

    @staticmethod
    def setup_args(parser) -> None:

        parser.add_argument("-j", "--json",
                            help="path to JSON export of PCAP file",
                            type=Path,
                            required=True,
                            action="store")

    def run(self) -> int:
        try:
            with open(self.args.json, "r") as f:
                logger.info(f"Reading PCAP dump from from `{str(self.args.json.absolute())}`")
                j = f.read()
        except FileNotFoundError:
            logger.critical(f"Unable to open {str(self.args.json.absolute())}")
            return 10

        logger.info("Parsing JSON PCAP file")

        for nr, direction, msg in deobfuscate(extract_from_json(j)):
            print(f"[{nr:05x}] {'OUT' if direction == 0 else ' IN'}:", end="")
            if len(msg) > 8 and msg[:2] == b"\xab\xab" and (msg[7] == 0x40 or msg[7] == 0x43):
                abab, cmd_length, payload_length, verb = unpack(">HHHH", msg[:8])
                logger.debug("%02x %02x %02x %02x", abab, cmd_length, payload_length, verb)
                for i in range(8):
                    print(f" {msg[i]:02x}", end="")
                for i in range(cmd_length-1):
                    if i%4 == 0:
                        print("\n            ", end="")
                    print(f" {msg[i+8]:02x}", end="")
                for i in range(payload_length):
                    if i%16 == 0:
                        print("\n            ", end="")
                    print(f" {msg[i+8+cmd_length-1]:02x}", end="")
                print(f"\n             {msg[-1]:02x}")
            else:
                for i in range(len(msg)):
                    if i % 16 == 0 and i != 0:
                        print("\n            ", end="")
                    print(f" {msg[i]:02x}", end="")
                print()

        return 0
