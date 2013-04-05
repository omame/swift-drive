# This module is used to send out emails to notify about swift-drive events.
# It is assumed that there is a MTA running on localhost on port 25 and
# that there aren't any restrictions or limitations.

import smtplib
from swift_drive.common.config import get_config
#from swift_drive.common.template import get_template


class Notification():
    def __init__(self):
        self.smtp_server = smtplib.SMTP('localhost')

    def send_notification(self, subject, body):
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

        for recipient in recipients:
            subject = '[swift-drive] - %s - %s' % (hostname, subject)
            message = 'From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s' % \
                      (sender, recipient, subject, body)
            # Try to send an email for 3 times before raising an exception
            for retries in range(4):
                if retries == 3:
                    msg = 'Failed to send an email to %s. Error: %s' % \
                          (recipient, e)
                    raise Exception(msg)
                try:
                    self.smtp_server.sendmail(sender, recipient, message)
                except Exception, e:
                    pass
                finally:
                    break
