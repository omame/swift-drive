from threading import Thread
from time import time
from swift_drive.common.config import get_config
from swift_drive.common.utils import exit
from os import getuid
from urllib2 import urlopen
try:
    import simplejson as json
except ImportError:
    import json


class RemoveDrives():
    def __init__(self):
        self.now = int(time())
        # Load the controller module
        try:
            conf_controller = get_config()['controller']
            controller = getattr(__import__('swift_drive.plugins.controller',
                                 fromlist=[conf_controller]), conf_controller)
            self.controller = controller.Controller()
        except:
            # A controller is necessary
            raise Exception('Failed to load %s controller module'
                            % conf_controller)

        # Load the backend module
        try:
            conf_backend = get_config()['backend']
            backend = getattr(__import__('swift_drive.plugins.backend',
                              fromlist=[conf_backend]), conf_backend)
            self.backend = backend.Backend()
        except:
            # A backend is necessary
            raise Exception('Failed to load %s backend module' % conf_backend)

        # Load the ticketing module
        try:
            conf_ticketing = get_config()['ticketing']
            ticketing = getattr(__import__('swift_drive.plugins.ticketing',
                                fromlist=[conf_ticketing]), conf_ticketing)
            self.ticketing = ticketing.Ticketing()
        except:
            # We can live without a ticketing system
            self.ticketing = None

        # Load the notification module
        try:
            conf_notification = get_config()['notification']
            notification = getattr(__import__(
                                   'swift_drive.plugins.notification',
                                   fromlist=[conf_notification]),
                                   conf_notification)
            self.notification = notification.Notification()
        except:
            # We can live without a notification system
            self.notification = None

    def remove_device(self, device_name):
        """
        Remove a device from the controller, create an event and, if
        configured, raise a ticket and send out a notification.

        :param device_name: The device name.
        """
        controller_id, vdisk_id = device_name.strip('c').split('u')
        # Check if the drive is present in the backend. If not, add it using
        # the information coming from the controller.
        device_info = self.backend.get_drive(device_name)
        if device_info is None:
            drive_info = self.controller.get_drive_from_device(device_name)
            drive_serial = drive_info['serial']
            self.backend.add_drive(device_name, drive_serial, self.now,
                                   drive_info['model'], drive_info['firmware'],
                                   drive_info['capacity'], 'failed')
        else:
            drive_serial = device_info['serial']
            # Check the backend if those drives are already being processed.
            # Exit if any.
            events = self.backend.get_event(drive_serial, status='new')
            events += self.backend.get_event(drive_serial, status='inprogress')
            if len(events) > 0:
                return
            self.backend.update_drive(device_name, drive_serial,
                                      status='failed')

        # Check if the drive had been already replaced in the past 24 hours
        a_day_ago = self.now - 86400
        events = self.backend.get_event(drive_serial, time=a_day_ago)
        if len(events) > 0:
            exit('The drive %s has been already replaced in the past 24h.\n'
                 'I am skipping it since it may be a false positive.')

        # At this point we are pretty sure the drive has to be replaced
        # First thing, fetch the drive information from the controller and
        # create an event to keep track of the operations, marking the drive
        # as failed.
        try:
            drive_info
        except:
            drive_info = self.controller.get_drive_from_device(device_name)

        self.backend.add_event(self.now, drive_serial, drive_info['status'],
                               'new', 1)
        # We can now try to remove the drive from the controller
        try:
            self.controller.remove_device(controller_id, vdisk_id)
        except Exception, msg:
            exit(msg)

        ################# Uncomment once ticketing is working #################
        # # We should now raise a ticket, if we want it
        # if self.ticketing is not None:
        #     try:
        #         ticket_number = self.ticketing.create()
        #     except Exception, msg:
        #         # We should exit if we can't raise a ticket. Since the status
        #         # of the event is still 'new' we will deal with this the next
        #         # time this command runs.
        #         exit(msg)
        #      finally:
        #          ticket_sent = True
        # # TODO: Add the ticket to the backend using the ticket_number
        #######################################################################

        # We can now update the event status to 'inprogress'
        try:
            self.backend.update_event(self.now, drive_info['serial'],
                                      status='inprogress')
        except Exception, msg:
            exit(msg)

        # Tell the sysops that the drive is being processed
        if self.notification is not None:
            try:
                msg = '%s has failed' % \
                      device_name
                # If we sent a ticket, say it in the notification
                try:
                    if ticket_sent:
                        msg += ' and I successfully raised a ticket'
                except:
                    pass
                self.notification.send_notification('Failed drive', msg)
                self.backend.update_event(self.now(), drive_info['serial'],
                                          notification_sent=1)
            except:
                # We can survive for now. If needed, we can send out the
                # notification later on.
                pass

    def main(self):
        """
        Detects failed drives and replaces them.
        """
        # # Only root can run this command, so check the UID first
        if getuid() > 0:
            exit('Only root can run this command', notify=False)

        # Get the list of unmounted drives from swift-recon. If there are more than
        # 3, stop and send out a notification: something bad is happening and it
        # requires manual intervention. In the future this value can be fetched
        # from the configuration file.
        for retries in range(4):
            if retries == 3:
                exit('Failed to connect to swift recon for 3 times.\n'
                     'Please check')
            try:
                recon_obj = urlopen('http://127.0.0.1:6000/recon/unmounted')
            except:
                continue
            if recon_obj.code == 200:
                try:
                    recon_list = json.loads(recon_obj.read())
                    unmounted_drives = [a['device'] for a in recon_list]
                except:
                    exit('Failed to load the json returned from swift-recon')
                break
            else:
                exit('Invalid HTTP code returned from swift-recon')

        if len(unmounted_drives) > 3:
            exit('Too many unmounted drives (currently %d). I\'m stopping here.'
                 '\nPlease investigate manually.')

        # Set up the thread pool
        threads = []
        for drive in unmounted_drives:
            threads.append(Thread(self.remove_drive(drive,)))

        # Start all threads
        [thread.start() for thread in threads]

        # Wait for all of them to finish
        [thread.join() for thread in threads]


def main():
    """
    Main entry point. Just invokes HandleFailedDrives.
    """
    return RemoveDrives().main()
