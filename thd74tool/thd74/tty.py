# -*- coding: utf-8 -*-

from logging import getLogger
from serial import Serial

logger = getLogger(__name__)


class GenericTHDTTY(object):
    """
    Serial communication for Kenwood TH series ham radios
    """

    def __init__(self, tty, timeout=0.2):
        """
        Serial connection class for Kenwood TH series handsets

        :param tty: str TTY device to use
        :param timeout: float default timeout for serial
        """
        self.tty = tty
        logger.debug(f"Connecting to {tty}")
        self.default_timeout = timeout
        self.s = Serial(tty, timeout=timeout)
        self.s.flushInput()
        self.s.flushOutput()

    def write(self, data):
        logger.debug("OUT: %s" % repr(data))
        return self.s.write(data)

    def read(self, *args, **kwargs):
        result = self.s.read(*args, **kwargs)
        logger.debug("  IN: %s", repr(result))
        if len(result) == 0:
            raise TimeoutError(f"{self.tty} read() timeout")
        return result

    def read_all(self):
        result = self.s.read_all()
        if len(result) == 0:
            raise TimeoutError(f"{self.tty} read_all() timeout")
        logger.debug("  IN: %s", repr(result))
        return result

    def read_line(self, *args, **kwargs):
        result = self.s.readline(*args, **kwargs)
        if len(result) == 0:
            raise TimeoutError(f"{self.tty} read_line() timeout")
        logger.debug("  IN: %s", repr(result))
        return result

    def available(self):
        return self.s.in_waiting

    def flush_input(self):
        if self.s.in_waiting > 0:
            logger.warning(f"{self.tty} flushing {self.s.in_waiting} bytes from input buffer")
        return self.s.flushInput()

    def flush_output(self):
        if self.s.out_waiting > 0:
            logger.warning(f"{self.tty} flushing {self.s.out_waiting} bytes from output buffer")
        return self.s.flushOutput()
