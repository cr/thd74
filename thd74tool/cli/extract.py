# -*- coding: utf-8 -*-

from logging import getLogger
from pathlib import Path

from .base import CliCommand
from ..thd74.binary import extract_from_exe, get_flash_blobs, identify_blob, count_blob_bytes, parse_blob
from ..thd74.crypto import decrypt_blob
from ..thd74.srec import make

logger = getLogger(__name__)


class ExtractCommand(CliCommand):

    name = "extract"
    help = "extract firmware data from updater"

    @staticmethod
    def setup_args(parser) -> None:

        parser.add_argument("-e", "--exe",
                            help="path to firmware updater .exe file",
                            type=Path,
                            required=True,
                            action="store")

        parser.add_argument("-p", "--path",
                            help="export firmware sections to path in SREC format",
                            type=Path,
                            action="store")

        parser.add_argument("-s", "--section",
                            help="select firmware section for export",
                            type=int,
                            action="append")

    def run(self) -> int:
        try:
            with open(self.args.exe, "rb") as f:
                logger.info(f"Reading updater from `{str(self.args.exe.absolute)}`")
                exe = f.read()
        except FileNotFoundError:
            logger.critical(f"Unable to open {str(self.args.exe.absolute)}")
            return 10

        logger.info("Parsing updater blobs")
        blobs = list(get_flash_blobs(extract_from_exe(exe)))
        sections = []
        for n, blob in zip(range(len(blobs)), blobs):
            section = identify_blob(blob, n)
            sections.append(section)
            if section is None:
                logger.warning(f"Unknown blob [{n}]")
            else:
                logger.info(f"Detected firmware section [{n}], looks like `{section['name']}` with permutation offet {section['permute_offset']}")
                section["size"] = count_blob_bytes(blob)

        if self.args.path is None:
            logger.info(f"Found {len(sections)} updater blobs")
            for n, s in zip(range(len(sections)), sections):
                if s is None:
                    print(f"[{n}]\tUNKNOWN BLOB\t0 bytes")
                else:
                    print(f"[{n}]\t{s['name']}\t{s['size']} bytes")
            logger.info("Now give ma a --path to write them to!")
            return 0

        if not self.args.path.is_dir():
            logger.critical(f"Unable to export to directory `{str(self.args.path.absolute())}` (must exist)")

        if self.args.section is None:
            export = [0, 1, 2, 3, 4]
        else:
            export = self.args.section
        
        for n in export:
            try:
                s = sections[n]
            except IndexError:
                logger.warning(f"Unable to export unknown section [{n}], skipping")
                continue
            file_name = self.args.path.absolute() / f"{s['name']}.srec"
            logger.info(f"Exporting section [{n}] to `{file_name}`")
            with open(file_name, "w") as f:
                for rec in make(32, parse_blob(decrypt_blob(blobs[n], s["permute_offset"], s["end_offset"]),
                                               s["memory_address"]), s["name"]):
                    f.write(rec)
                    
        return 0
