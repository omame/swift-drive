from threading import Thread
from time import time
from swift_drive.common.config import get_config
from swift_drive.common.utils import exit
from os import geteuid
from urllib2 import urlopen
try:
    import simplejson as json
except ImportError:
    import json

now = int(time())


class HandleFailedDrives():
    def __init__(self):
        # Load the controller module
        try:
            conf_controller = get_config()['controller']
            controller = getattr(__import__('swift_drive.plugins.controller',
                                 fromlist=[conf_controller]), conf_controller)
            self.controller = controller.Controller()
        except:
            raise Exception('Failed to load %s controller module'
                            % conf_controller)

        # Load the backend module
        try:
            conf_backend = get_config()['backend']
            backend = getattr(__import__('swift_drive.plugins.backend',
                              fromlist=[conf_backend]), conf_backend)
            self.backend = backend.Backend()
        except:
            raise Exception('Failed to load %s backend module' % conf_backend)

        # Load the ticketing module
        try:
            conf_ticketing = get_config()['ticketing']
            ticketing = getattr(__import__('swift_drive.plugins.ticketing',
                                fromlist=[conf_ticketing]), conf_ticketing)
            self.ticketing = ticketing.Ticketing()
        except:
            # We can live without a ticketing system
            pass

    def replace_drive(self, device_name):
        """
        Replaces a drive from the queue
        """
        drive_info = self.controller.get_drive_from_device(device_name)
        # Check the backend if those drives are already being processed
        events = self.backend.get_event(drive_info['serial'])

        # Check if the drive had been already replaced in the past 24 hours
        #now - 86400

    def main(self):
        """
        Detects failed drives and replaces them.
        """
        # Only root can run this command, so check the UID first
        if geteuid != 0:
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
            threads.append(Thread(self.replace_drive, args=(drive,)))

        # Start all threads
        [thread.start() for thread in threads]

        # Wait for all of them to finish
        [thread.join() for thread in threads]

        # Clean up the each failed drive and raise a ticket to replace it
        pass
