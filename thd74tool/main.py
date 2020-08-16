#!usr/bin/env python3
# -*- coding: utf-8 -*-

import atexit
from argparse import ArgumentParser
from logging import getLogger
from sys import exit, argv, stdout

import coloredlogs
from pkg_resources import require

import thd74tool.cli

coloredlogs.DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
coloredlogs.install(level="INFO")
logger = getLogger(__name__)


def get_args(args=None):
    """
    Argument parsing
    :return: Argument parser object
    """

    pkg_version = require("thd74tool")[0].version

    parser = ArgumentParser(prog="thd74tool")
    parser.add_argument("--version", action="version", version="%(prog)s " + pkg_version)

    parser.add_argument("--debug",
                        help="enable debug logging",
                        action="store_true")

    parser.add_argument("-t", "--tty",
                        help="force path or port for serial device",
                        type=str,
                        action="store")

    # Set up subparsers, one for each command
    subparsers = parser.add_subparsers(help="sub command", dest="command")
    commands_list = thd74tool.cli.list_commands()
    for command_name in commands_list:
        command_class = commands_list[command_name]
        sub_parser = subparsers.add_parser(command_name, help=command_class.help)
        command_class.setup_args(sub_parser)

    return parser.parse_args(args or argv[1:])


# @atexit.register
# def at_exit():
#     logger.debug("Waiting for backround threads")
#     Simulator.stop_instances()
#     Simulator.join_instances()
#     logger.debug("Backround threads finished")


# This is the entry point used in setup.py
def main(main_args=None) -> int:
    global logger

    args = get_args(main_args)

    if args.debug:
        coloredlogs.DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
        coloredlogs.install(level="DEBUG")

    logger.debug("Command arguments: %s" % args)

    try:
        result = thd74tool.cli.run(args)

    except KeyboardInterrupt:
        stdout.write("\n")
        stdout.flush()
        logger.critical("User abort")
        result = 5

    return result