# -*- coding: utf-8 -*-

from logging import getLogger

from .base import CliCommand
from ..thd74.device import enumerate

logger = getLogger(__name__)


class DevicesCommand(CliCommand):

    name = "devices"
    help = "enumerate detected devices"

    def run(self):
        devices = enumerate()
        if len(devices) > 0:
            for device in devices:
                mode = "unknown mode (BE CAREFUL)"
                if device.comm.pcrig_mode:
                    mode = "PCRIG mode"
                    fv = f"firmware {device.comm.get_firmware_version()}"
                if device.comm.fwprog_mode:
                    mode = "FWPROG mode"
                    fv = None
                if not device.comm.thd_hardware:
                    mode = "unknown hardware (BE CAREFUL)"
                    fv = None
                print(f"[{devices.index(device)}]\t{device.tty}\t{device.brand}\t{device.model}\t{mode}\t{fv}")
            return 0

        else:
            logger.critical("No device detected. Is it connected?")
            return 10
