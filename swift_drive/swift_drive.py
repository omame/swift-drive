#!/usr/bin/python
import sys
from swift_drive.common import config, utils


class swift_drive(object):
    """
    Command line interface for swift-drive

    :param args: The command line arguments to process
    """
    def __init__(self, args=None):
        self.args = args
        if not self.args:
            self.args = sys.argv
        self.action = self.args[0]

        # Load the controller module
        controller_type = config.get_config('controller_type')
        try:
            self.controller = getattr(__import__(swift_drive.plugins.controllers,
                                                 fromlist=[controller_type]),
                                      controller_type)
        except:
            utils.exit('Failed to load %s controller module' % controller_type, 1)

        # Load the ticketing module
        ticketing_system = config.get_config('ticketing_system')
        try:
            self.ticketing = getattr(__import__(swift_drive.plugins.ticketing,
                                                fromlist=[ticketing_system]),
                                     ticketing_system)
        except:
            utils.exit('Failed to load %s ticketing module' % ticketing_system, 1)

        # Load the ticketing module
        backend = config.get_config('backend')
        try:
            self.backend = getattr(__import__(swift_drive.plugins.backend,
                                              fromlist=[backend]),
                                   backend)
        except:
            utils.exit('Failed to load %s backend module' % backend, 1)

