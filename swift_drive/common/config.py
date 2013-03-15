from ConfigParser import ConfigParser

# CONFIG_FILE = '/etc/swift-drive/swift-drive.conf'
# This is for testing
CONFIG_FILE = '/home/dvaleriani/swift-drive/etc/swift-drive.conf-sample'


class ConfigFileError(Exception):
    pass


def get_config(config_file=CONFIG_FILE):
    """
    Get the value for the specified key in the config file.

    :param config_file: The configuration file to read.
    :returns: A dictionary with the configuration values.
    """
    c = ConfigParser()
    try:
        c.read(config_file)
        return dict(c.items('swift-drive'))
    except Exception, e:
        raise ConfigFileError("Error trying to load config %s: %s" %
                             (config_file, e))
