import ConfigParser

# CONFIG_FILE = '/etc/swift-drive/swift-drive.conf'
# This is for testing
CONFIG_FILE = '/home/dvaleriani/swift-drive/etc/swift-drive.conf-sample'


class ConfigFileError(Exception):
    pass


conf = ConfigParser.ConfigParser()
try:
    conf.read(CONFIG_FILE)
except ConfigParser.Error, e:
    raise ConfigFileError("Error trying to load config {0}: {1}".format(
                          CONFIG_FILE, e))


def get_config(section="common"):
    """
    Get the values for the specified section in the config file.

    :param config_file: The configuration file to read.
    :returns: A dictionary with the configuration values.
    """
    try:
        return dict(conf.items(section))
    except ConfigParser.Error, e:
        raise ConfigFileError("Error reading conf section {0}: {1}".format(
                             section, e))

