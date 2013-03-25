# This module is used to send out emails to notify about swift-drive events.
# It is assumed that there is a MTA running on localhost on port 25 and
# that there aren't any restrictions or limitations.

import smtplib
from swift_drive.common.config import get_config
#from swift_drive.common.template import get_template


def send_notification(subject, msg):
    # Get the list of recipients from the config file.
    # The option is notification_email_recipients
    from swift_drive.common.utils import get_hostname
    hostname = get_hostname()
    config = get_config()
    # Get the recipients from the configuration. We can't go any further
    # without any.
    try:
        recipients = config['notification_email_recipients'].split(',')
    except:
        raise Exception('Error: could not find any recipients in the '
                        'configuration file. Please configure at least one.')

    # Check if there is a specific sender configured.
    try:
        sender = config['notification_email_from']
    except:
        sender = 'alert@swift-drive.com'

    try:
        message = '[swift-drive] - %s - %s/r/n/r/n%s' % (hostname, subject, msg)
        server = smtplib.SMTP('localhost')
        server.set_debuglevel(0)
        server.sendmail(sender, recipients, message)
        server.quit()
    except:
        # TODO: It should try again for a few times
        raise
    return True
