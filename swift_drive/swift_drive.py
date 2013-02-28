#!/usr/bin/python
import re
import sys
import urllib2

try:
    from simplejson import json
except ImportError:
    import json

from ConfigParser import ConfigParser


def _exit(msg, error_code=1):
    '''
    Exit with a specific error code (default 2)
    :msg: Message to be returned
    :error_code: Exit code
    '''
    print msg
    exit(error_code)


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
        controller_type = self.get_config('controller_type')
        try:
            ctl = getattr(__import__(swift_drive.plugins.controllers,
                                fromlist=[controller_type]), controller_type)
        except:
            _exit('Failed to load %s controller module' % controller_type, 1)

    def execute(self):
        if self.action == 'getfailed':
            self.getfailed()
        elif self.action == 'replace':
            self.replace()

    def getfailed():
        pass

    def replace():
        pass

    def eject():
        pass

    def get_recon_unmounted():
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

    def get_config(key):
        """
        Get the value for the specified key in the config file

        :param key: configfile: The location of the config file to be parsed
        :returns: The value for the requested key
        """
        configfile = '/etc/swift-drive/swift-drive.conf'
        c = ConfigParser()
        if not c.read(configfile):
            print "Unable to read config file: %s" % configfile
            exit(1)
        try:
            return str(c.get('swift-drive', key))
        except:
            return False
