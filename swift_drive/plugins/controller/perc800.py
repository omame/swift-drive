import re
from swift_drive.common.utils import execute, get_binaries
from swift_drive.common import disk
from swift_drive.common.config import get_config

COMMANDS = ['omconfig', 'omreport']


class Controller():
    def __init__(self):
        """
        Initialise the binaries for the controller. Prefer those specified in
        the config file to the ones in $PATH. Raise an exception in case at
        least one isn't usable.

        Binaries dictionary format:
        {'omconfig': '/path/to/omconfig', 'omreport': '/path/to/omreport'}

        """
        config = get_config()
        try:
            binaries = config['controller_binaries']
            self.binaries = dict([(a.split('/')[-1].strip(), a.strip())
                                 for a in binaries.split(', ')])
        except Exception, e:
            self.binaries = get_binaries(COMMANDS)
            if COMMANDS != sorted(self.binaries.keys()):
                msg = 'Error trying to locate the omtools binaries: %s' % e
                raise Exception(msg)

    def get_drive_from_device(self, device_name):
        """
        Collects information about a drive using the device name.

        :param device_name: The device name.
        :returns: A dictionary that contains two dictionaries with the collected
                  relevant information about the device.
        """
        controller, vdisk_id = device_name.strip('c').split('u')
        return self.get_drive_from_controller(controller, vdisk_id)

    def get_drive_from_controller(self, controller, vdisk_id):
        """
        Collects information about a drive using controller coordinates.

        :param controller: The controller index.
        :param vdisk_id: The id of the vdisk to get the information for.
        :returns: A dictionary that contains two dictionaries with the collected
                  relevant information about the device.
        """
        controller = str(controller)
        vdisk_id = str(vdisk_id)
        results = {}
        pdisk = {}
        vdisk = {}
        for name in 'pdisk', 'vdisk':
            d = eval(name)
            cmd = '%s storage %s controller=%s vdisk=%s' % \
                  (self.binaries['omreport'], name, controller, vdisk_id)
            res = execute(cmd)
            # Exit if we catch an error message
            if re.match(r'^Error:*', res[0]):
                raise Exception("Error: Unable to get drive info for vdisk %s\n"
                                "Omreport error: %s") % (vdisk_id, res[0])
            else:
                # The perc controller is attached to a slot and we need to know
                # its id otherwise is pointless to go any further
                try:
                    d['slot'] = re.findall(r'Slot \d', res[1])[0][-1]
                except:
                    msg = ("Error: can't fetch the slot number.\n"
                           "Probably the drive has been removed already.\n"
                           "Controller: %s, vdisk: %s") % (controller, vdisk_id)
                    raise Exception(msg)

                # We can split everything after the second element by ':'
                # so we will have a very nice dictionary (with 0 effort)
                for element in res[2:]:
                    key, value = element.split(':', 1)
                    d[key.lower().strip()] = value.lower().strip()
                results['%s_status' % name] = d['status']
            name = d

        results['port'] = pdisk['id']
        results['serial'] = pdisk['serial no.']
        results['model'] = pdisk['product id']
        results['firmware'] = pdisk['revision']
        results['slot'] = pdisk['slot']
        capacity = pdisk['capacity'].split()[0].split('.')[0]
        results['capacity'] = capacity.replace(',', '.')[:4] + ' TB'
        results['status'] = pdisk['status']
        return results

    def remove_device(self, controller, vdisk_id):
        # TODO: Check on device xfs errors and bad mount. mtab
        """
        Remove a device from the controller given a specific port. Turns the
        indicator light on for the port and, if everything goes well, it will go
        ahead and attempt to have the device removed.

        :param controller: The controller id.
        :param vdisk_id: The id of the vdisk to remove.
        :returns: A boolean value that reflects the result of the operation.
        """
        controller = str(controller)
        vdisk_id = str(vdisk_id)
        device_id = 'c%su%s' % (controller, vdisk_id)
        drive_info = self.get_drive_from_controller(controller, vdisk_id)
        pdisk_id = drive_info['port']
        # First try to turn the indicator light on for the device port
        try:
            self.led('blink', controller, pdisk_id)
        except:
            # We'll just pass for now. In the future it'd be cool to get
            # notified when this happens. TODO
            pass

        # Then check if the device is not mounted
        if disk.is_mounted(device_id):
            disk.umount(device_id)

        # If all goes well then proceed with removing the device unit
        removal_cmd = ('%s storage vdisk action=deletevdisk controller=%s '
                       'vdisk=%s' % (self.binaries['omconfig'],
                       controller, vdisk_id))
        removal_result = execute(removal_cmd)
        if not 'Command successful!' in removal_result[0]:
            raise Exception("Error: Failed to remove vdisk %s from "
                            "controller %s for pdisk %s\n"
                            "Omconfig error: %s ") % \
                           (vdisk_id, controller, pdisk_id, removal_result[0])

    def add_device(self, controller, vdisk_id, pdisk_id, format=True):
        """
        Add a device back into the system.

        :param controller: The controller id.
        :param vdisk_id: The id of the vdisk that should be created.
        :param pdisk_id: The id of the pdisk to add.
        :param format: Specifies wheter or not the drive should be formatted.
        :returns: A boolean value that reflects the result of the operation.
        """
        controller = str(controller)
        pdisk_id = str(pdisk_id)
        device_id = 'c%su%s' % (controller, vdisk_id)
        device_name = device_id + 'p'
        # drive_info = get_drive_info(controller, vdisk_id)

        # Check if there is a replace operation in progress. INPROGRESS
        # Backend still needs to be develped.
        # Should also allow --force to override. TODO
        # backend_info = backend.get_drive(vdisk_id, in_inprogress=True)
        # pdisk_id = backend_info['pdisk']
        # if backend_info['inprogress'] == True:
        #     pass
        # else:
        #     pass
        # pdisk_id = drive_info['port']
        # remove_device(controller, vdisk_id)
        #####
        # Sometimes after a drive has been swapped the vdisk is recreated right
        # away. We need to check this and clean up if necessary.
        # if drive_info['vdisk_status']:  # TOCHECK
        #     remove_device(controller, vdisk_id)

        # Now that we cleaned up the vdisk we can move on and create the new one
        add_cmd = '%s storage controller action=createvdisk controller=%s ' \
            'pdisk=%s raid=r0 size=max stripesize=64kb diskcachepolicy=disabled ' \
            'readpolicy=ara writepolicy=wb' % \
            (self.binaries['omconfig'], controller, pdisk_id)
        add_result = execute(add_cmd)
        if not 'Command successful!' in add_result[0]:
            raise Exception("Cannot create vdisk on port %s for controller %s.\n"
                            "Error: %s ") % \
                           (pdisk_id, controller, str(add_result))

        """
        Device added, so partition and format it
        """
        if format:
            disk.format_drive(device_name, '3T', device_id)
        """
        Now let's mount the device back into the system
        """
        disk.mount(device_id)
        """
        Let's go ahead and turn the indicator light off
        """
        try:
            self.led('unblink', controller, pdisk_id)
        except:
            # We'll just pass for now. In the future it'd be cool to get
            # notified when this happens. TODO
            pass

    def led(self, action, controller, pdisk_id):
        '''
        Switch on or off the indicator led for a specific pdisk.

        :param action: The action to take. Could be blink|unblink, on|off or 0|1.
        :param controller: The controller id.
        :param pdisk_id: The pdisk id (also known as port). Example: 1:0:18
        :returns: A boolean value that reflects the result of the operation.
        '''
        if action in ['on', 'blink', 1]:
            action = 'blink'
        elif action in ['off', 'unblink', 0]:
            action = 'unblink'
        else:
            raise Exception('Operation not recognised')

        indicator_cmd = '%s storage pdisk action=%s controller=%s pdisk=%s' \
            % (self.binaries['omconfig'], action, controller, pdisk_id)
        indicator_result = execute(indicator_cmd)
        if not 'Command successful!' in indicator_result[0]:
            msg = ("Error: Failed to turn the indicator light off "
                   "for pdisk %s on controller %s.\n"
                   "Error: %s ") % (pdisk_id, controller,
                                    indicator_result[0])
            raise Exception(msg)
