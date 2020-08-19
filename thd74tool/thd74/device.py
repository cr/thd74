# -*- coding: utf-8 -*-

from logging import getLogger
from serial.tools import list_ports

from .config import THD74Config
from .protocol import THD74Protocol

logger = getLogger(__name__)


def enumerate(force_device=None, force_model=None):

    global models

    devices = []

    if force_device is None and force_model is None:
        for model in models.values():
            devices += enumerate_model(model)
        return devices

    elif force_device is not None and force_model is None:

        if force_device.isdecimal():
            # User addressed device by its numeric selector
            for model in models.values():
                devices += enumerate_model(model)
            try:
                return [devices[int(force_device)]]
            except IndexError:
                logger.error(f"Invalid numeric device selector {force_device}")
                return []

        # Device is given as tty spec
        return [THD74(force_device)]

    elif force_device is not None and force_model is not None:

        try:
            model = models[force_model.upper()]
        except KeyError:
            logger.critical(f"Invalid model specifier `{force_model}`")
            return []

        return [model(force_device)]

    logger.critical("Unable to detect device")
    return []


def enumerate_model(thd_device) -> list:

    devices = []

    for d in list_ports.comports():
        if d.vid == thd_device.usb_vendor_id and d.pid == thd_device.usb_product_id:
            if not d.product == thd_device.usb_product_name:
                logger.warning(f"Unexpected serial device product `{d.product}` (BE CAREFUL)")
            devices.append(thd_device(d.device))

    return devices


class THD74(object):
    """
    Device object for Standard Horizon HX870 maritime radios
    """
    handle = "THD74"
    brand = "Kenwood"
    model = "TH-D74"
    usb_vendor_id = 0x2166
    usb_vendor_name = "JVC KENWOOD"
    usb_product_id = 0x600b
    usb_product_name = "TH-D74"

    protocol_model = THD74Protocol
    config_model = THD74Config

    def __init__(self, tty):
        self.tty = tty
        self.comm = self.protocol_model(tty=tty)
        self.pcrig_mode = None
        self.fwprog_mode = None
        self.firmware_version = None
        self.__init_config()

    def __init_config(self):
        # See what we're talking to on that tty
        if self.comm.thd_hardware:
            if self.comm.pcrig_mode:
                self.config = None
                self.fwprog_mode = None
                self.firmware_version = "V1.10"
                logger.info(f"Device on {self.tty} is {self.handle} in PCRIG mode")
            elif self.comm.fwprog_mode:
                self.config = self.config_model(self.comm)
                self.pcrig_mode = None
                logger.info(f"Device on {self.tty} is {self.handle} in FWPROG mode")
            elif not self.comm.fwprog_mode and not self.comm.pcrig_mode:
                self.config = None
                logger.warning(f"Device on {self.tty} is {self.handle} in unknown mode")
                logger.critical("This should never happen. Please file an issue on GitHub.")
            else:
                self.config = self.config_model(self.comm)
                logger.warning(f"Device on {self.tty} is {self.handle} reports both PCRIG and FWPROG mode")
                logger.critical("This should never happen. Please file an issue on GitHub.")
        else:
            logger.error(f"Device on {self.tty} does not behave like HX hardware")

    @property
    def is_fwprog_mode(self) -> bool:
        return self.comm.fwprog_mode

    def __str__(self):
        return f"{self.brand} {self.handle} on `{self.tty} [{'FWPROG mode' if self.comm.fwprog_mode else 'PCRIG mode'}]`"


models = {}
for model_class in [THD74]:
    models[model_class.handle.upper()] = model_class
del model_class
