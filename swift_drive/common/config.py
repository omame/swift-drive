from ConfigParser import ConfigParser
from swift_drive.common.utils import exit


def get_config(key, config_file='/etc/swift-drive/swift-drive.conf'):
    """
    Get the value for the specified key in the config file.

    :param key: The config parameter to get.
    :param config_file: The location of the config file to be parsed.
    :returns: The value for the requested key.
    """
    c = ConfigParser()
    try:
        if not c.read(config_file):
            print "Unable to read config file: %s" % config_file
            exit(1)
        return str(c.get('swift-drive', key))
    except:
        return False

