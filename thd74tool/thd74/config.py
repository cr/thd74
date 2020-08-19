# -*- coding: utf-8 -*-

from binascii import hexlify, unhexlify
from logging import getLogger

from .protocol import GenericTHDProtocol, ProtocolError

logger = getLogger(__name__)


class GenericTHDConfig(object):

    def __init__(self, protocol: GenericTHDProtocol):
        self.p = protocol

    def config_read(self, progress=False):
        return b''

    def config_write(self, data, check_region=True, progress=False):
        pass


class THD74Config(GenericTHDConfig):
    pass
