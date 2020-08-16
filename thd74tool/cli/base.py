# -*- coding: utf-8 -*-

from logging import getLogger

logger = getLogger(__name__)


class CliCommand(object):
    """
    Generic parent class for cli command implementations
    """

    name = "Template"
    help = "Just a parent class for CLI commands"

    @staticmethod
    def setup_args(parser) -> None:
        """
        Add a subparser for the command's specific arguments.
        This definition serves as default, but commands are free to
        override it.
        :param parser: parent argparser to add to
        :return: None
        """
        pass

    @staticmethod
    def check_args(args) -> bool:
        """
        Validate command args
        :param args: parsed arguments object
        :return: bool
        """
        del args
        return True

    def __init__(self, args):
        self.args = args

    def setup(self) -> bool:
        """
        Performs all the setup shared among multiple runs of the command.
        Put everything here that takes too long for __init__().
        :return: bool
        """
        return True

    def run(self) -> int:
        """
        Executes the the steps that constitutes the actual run.
        Results are kept internally in the class instance.
        :return: int failure state
        """
        return 0

    def teardown(self):
        """
        Clean up steps required after runs were performed.
        :return: None
        """
        pass


def __subclasses_of(cls):
    sub_classes = cls.__subclasses__()
    sub_sub_classes = []
    for sub_cls in sub_classes:
        sub_sub_classes += __subclasses_of(sub_cls)
    return sub_classes + sub_sub_classes


def list_commands():
    """Return a list of all cli commands"""
    return dict([(command.name, command)
                 for command in __subclasses_of(CliCommand)])


def run(args) -> int:
    all_commands = list_commands()

    if args.command is None:
        args.command = "info"

    try:
        current_command = all_commands[args.command](args)
    except KeyError:
        logger.critical("Unknown command `%s`" % args.command)
        return 5

    if not current_command.check_args(args):
        return 5

    try:
        logger.debug("Running command .setup()")
        if not current_command.setup():
            logger.critical("Setup failed")
            return 10
        logger.debug("Running command .run()")
        result = current_command.run()

    except KeyboardInterrupt:
        logger.debug("Running command .teardown()")
        current_command.teardown()
        raise KeyboardInterrupt

    logger.debug("Running command .teardown()")
    current_command.teardown()

    return result
