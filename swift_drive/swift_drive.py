#!/usr/bin/python
import re
import sys
import urllib2
from swift_drive.common import config, utils

try:
    from simplejson import json
except ImportError:
    import json


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

    def get_unmounted_drives():
        """
        Get unmounted drives information from swift-recon
        """
        ip_address = '127.0.0.1'
        port = '6000'
        url = 'http://%s:%s/recon/unmounted' % (ip_address, port)

        retries = 0
        timeout = 10
        while (retries < 3):
            try:
                urlobj = urllib2.urlopen(url, timeout=timeout)
                break

            except urllib2.URLError, e:
                if str(e.reason) == 'timed out':
                    retries = retries + 1
                    timeout += 5

            except urllib2.HTTPError, e:
                print "Error code: %s" % e.code
                raise

        if retries == 3:
            exit(1)

        if re.match(r'^2[0-9][0-9]$', str(urlobj.code).strip()):
            body = urlobj.read()
            content = json.loads(body)

        return content

