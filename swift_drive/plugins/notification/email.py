# This module is used to send out emails to notify about swift-drive events.
# It is assumed that there is a MTA running on localhost on port 25 and
# that there aren't any restrictions or limitations.

import smtplib
from swift_drive.common.config import get_config
#from swift_drive.common.utils import get_hostname
#from swift_drive.common.template import get_template


def send_notification(subject, msg):
    # Get the list of recipients from the config file.
    # The option is notification_email_recipients
    hostname = get_hostname()
    recipients = get_config('notification_email_recipients').split(',')
    sender = get_config('notification_email_from')
    if not sender:
        sender = 'alert@swift-drive.com'

    try:
        message = subject + msg
        server = smtplib.SMTP('localhost')
        server.set_debuglevel(0)
        server.sendmail(sender, recipients, message)
        server.quit()
    except:
        # TODO: It should try again for a few times
        raise
    return True
