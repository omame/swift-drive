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
        controller_id, vdisk_id = device_name.strip('c').split('u')
        return self.get_drive_from_controller(controller_id, vdisk_id)

    def get_drive_from_controller(self, controller_id, vdisk_id):
        """
        Collects information about a drive using controller coordinates.

        :param controller_id: The controller index.
        :param vdisk_id: The id of the vdisk to get the information for.
        :returns: A dictionary that contains two dictionaries with the collected
                  relevant information about the device.
        """
        controller_id = str(controller_id)
        vdisk_id = str(vdisk_id)
        results = {}
        pdisk = {}
        vdisk = {}
        for name in 'pdisk', 'vdisk':
            d = eval(name)
            cmd = '%s storage %s controller=%s vdisk=%s' % \
                  (self.binaries['omreport'], name, controller_id, vdisk_id)
            res = execute(cmd)
            # Exit if we catch an error message
            if re.match(r'^Error:*', res[0]):
                raise Exception("Error: Unable to get drive info for vdisk %s\n"
                                "Omreport error: %s") % (vdisk_id, res[0])
            else:
                # The embedded controller doesn't have a slot
                if controller_id == '0':
                    d['slot'] = 'embedded'
                else:
                    # The perc controller is attached to a slot and we need to know
                    # its id otherwise is pointless to go any further
                    try:
                        d['slot'] = re.findall(r'Slot \d', res[1])[0][-1]
                    except:
                        msg = ("Error: can't fetch the slot number.\n"
                               "Probably the drive has been removed already.\n"
                               "Controller: %s, vdisk: %s") % \
                              (controller_id, vdisk_id)
                        raise Exception(msg)

                # We can split everything after the second element by ':'
                # so we will have a very nice dictionary (with 0 effort)
                for element in res[2:]:
                    key, value = element.split(':', 1)
                    d[key.lower().strip()] = value.lower().strip()
            name = d

        results['port'] = pdisk['id']
        results['serial'] = pdisk['serial no.'].upper()
        results['model'] = pdisk['product id'].upper()
        results['firmware'] = pdisk['revision'].upper()
        results['controller_slot'] = pdisk['slot']
        capacity = pdisk['capacity'].split()[0].split('.')[0]
        results['capacity'] = capacity.replace(',', '.')[:4] + ' TB'
        # Use a consistent status by translating what the controller returns
        if pdisk['state'] == 'online':
            results['status'] = 'active'
        elif pdisk['state'] == 'critical':
            results['status'] = 'failed'
        else:
            results['status'] = 'unknown'
        return results

    def remove_device(self, controller_id, vdisk_id):
        # TODO: Check on device xfs errors and bad mount. mtab
        """
        Remove a device from the controller given a specific port. Turns the
        indicator light on for the port and, if everything goes well, it will go
        ahead and attempt to have the device removed.

        :param controller_id: The controller id.
        :param vdisk_id: The id of the vdisk to remove.
        :returns: A boolean value that reflects the result of the operation.
        """
        controller_id = str(controller_id)
        vdisk_id = str(vdisk_id)
        device_id = 'c%su%s' % (controller_id, vdisk_id)
        drive_info = self.get_drive_from_controller(controller_id, vdisk_id)
        pdisk_id = drive_info['port']
        # First try to turn the indicator light on for the device port
        try:
            self.switch_led('blink', controller_id, pdisk_id)
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
                       controller_id, vdisk_id))
        removal_result = execute(removal_cmd)
        if not 'Command successful!' in removal_result[0]:
            raise Exception("Error: Failed to remove vdisk %s from "
                            "controller %s for pdisk %s\n"
                            "Omconfig error: %s ") % \
                           (vdisk_id, controller_id, pdisk_id, removal_result[0])

    def add_device(self, controller_id, vdisk_id, pdisk_id, format=True):
        """
        Add a device back into the system.

        :param controller_id: The controller id.
        :param vdisk_id: The id of the vdisk that should be created.
        :param pdisk_id: The id of the pdisk to add.
        :param format: Specifies wheter or not the drive should be formatted.
        :returns: A boolean value that reflects the result of the operation.
        """
        controller_id = str(controller_id)
        pdisk_id = str(pdisk_id)
        device_id = 'c%su%s' % (controller_id, vdisk_id)
        device_name = device_id + 'p'
        # drive_info = get_drive_info(controller_id, vdisk_id)

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
        # remove_device(controller_id, vdisk_id)
        #####
        # Sometimes after a drive has been swapped the vdisk is recreated right
        # away. We need to check this and clean up if necessary.
        # if drive_info['vdisk_status']:  # TOCHECK
        #     remove_device(controller_id, vdisk_id)

        # Now that we cleaned up the vdisk we can move on and create the new one
        add_cmd = '%s storage controller action=createvdisk controller=%s ' \
                  'pdisk=%s raid=r0 size=max stripesize=64kb ' \
                  'diskcachepolicy=disabled readpolicy=ara writepolicy=wb' % \
                  (self.binaries['omconfig'], controller_id, pdisk_id)
        add_result = execute(add_cmd)
        if not 'Command successful!' in add_result[0]:
            raise Exception("Cannot create vdisk on port %s for controller %s.\n"
                            "Error: %s ") % \
                           (pdisk_id, controller_id, str(add_result))

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
            self.switch_led('unblink', controller_id, pdisk_id)
        except:
            # We'll just pass for now. In the future it'd be cool to get
            # notified when this happens. TODO
            pass

    def switch_led(self, action, controller_id, pdisk_id):
        '''
        Switch on or off the indicator led for a specific pdisk.

        :param action: The action to take. Could be blink|unblink, on|off or 0|1.
        :param controller_id: The controller id.
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
            % (self.binaries['omconfig'], action, controller_id, pdisk_id)
        indicator_result = execute(indicator_cmd)
        if not 'Command successful!' in indicator_result[0]:
            msg = ("Error: Failed to turn the indicator light off "
                   "for pdisk %s on controller %s.\n"
                   "Error: %s ") % (pdisk_id, controller_id,
                                    indicator_result[0])
            raise Exception(msg)

    def get_controllers(self):
        '''
        Extract information for the controllers.

        :returns: A dictionary with the id and PCI slot.
        '''
        cmd = '%s storage controller' % self.binaries['omreport']
        result = execute(cmd)
        filtered_result = [a for a in result
                           if a.startswith('ID') or a.startswith('Slot ID')]
        controllers = {}
        for n in range(0, len(filtered_result), 2):
            controller_id = filtered_result[n].split(':')[1].strip()
            slot_id = filtered_result[n + 1].split(':')[1].strip()
            controllers[controller_id] = slot_id
        return controllers

    def get_ports(self, controller_id):
        '''
        Extract information for the ports.
        NOTE: A drive must be inserted for the port to be detected. As far as
        I'm aware the perc800 controller has no way to get the ports status
        when empty. So in this case it would be more appropriate to say that
        we're returning the list of pdisks.

        :param controller_id: The controller to inspect.
        :returns: A dictionary with the information about the ports. Format:
                  {port_id: (status, drive_serial)}
        '''
        cmd = '%s storage pdisk controller=%s' % (self.binaries['omreport'],
                                                  controller_id)
        result = execute(cmd)
        filtered_result = [a for a in result if a.startswith('ID')
                           or a.startswith('State')
                           or a.startswith('Serial No.')]
        ports = {}
        for n in range(0, len(filtered_result), 3):
            port_id = ':'.join(filtered_result[n].split(':')[1:]).strip()
            port_status = filtered_result[n + 1].split(':')[1].strip()
            # Use a consistent status by translating what the controller returns
            if port_status == 'Online':
                port_status = 'active'
            elif port_status in ['Failed', 'Foreign']:
                port_status = port_status.lower()
            else:
                port_status = 'unknown'
            port_serial = filtered_result[n + 2].split(':')[1].strip()
            ports[port_id] = (port_status, port_serial)
        return ports

    def get_all_drives(self, controller_id):
        '''
        Extract information all the drives for a given controller. This is
        used when initialising the backend. It usually takes a while to run.
        NOTE: Any missing vdisks will be skipped.

        :param controller_id: The controller to inspect.
        :returns: A dictionary with the information about the drives.
        '''
        # First fetch the list of the vdisks
        cmd = '%s storage vdisk controller=%s' % (self.binaries['omreport'],
                                                  controller_id)
        vdisks = [a.split(':')[1].strip() for a in execute(cmd)
                  if a.startswith('ID')]
        # Now let's use the list to extract information for each drive
        all_drives = {}
        for vdisk_id in vdisks:
            device_id = 'c%su%s' % (controller_id, vdisk_id)
            try:
                all_drives[device_id] = self.get_drive_from_controller(
                                            controller_id, vdisk_id)
            except:
                print device_id + ' had problems'
        return all_drives
