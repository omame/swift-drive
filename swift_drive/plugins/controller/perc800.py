import re
from swift_drive.common import utils, config

COMMANDS = ['omconfig', 'omreport']

# First of all check if omreport and omconfig are usable.
# We need to check if there is an override in the config file and create
# a dictionary with the specified binaries
binaries = config.get_config('controller_binaries', 'etc/swift-drive.conf-sample')
if binaries:
    binaries = dict([(a.split('/')[-1], a) for a in binaries.split(', ')])
else:
    binaries = utils.get_binaries(COMMANDS)
    if COMMANDS != sorted(binaries.keys()):
        utils.exit('Error locating binaries for the perc800 controller motule')
# binaries now should contain a dictionary like this
# {'omconfig': '/path/to/omconfig', 'omreport': '/path/to/omreport'}


def get_drive_info(controller, vdisk_id):
    """
    Collects information about a device on provided controller & device

    :param controller: The controller index.
    :param vdisk_id: The id of the vdisk to get the information for.
    :returns: A dictionary that contains two dictionaries with the collected
              relevant information about the device.
    """
    # TODO: All those exits should trigger a notification. I think this should
    #       be handled by utils.exit, not here.
    controller = str(controller)
    vdisk_id = str(vdisk_id)
    results = {}
    pdisk = {}
    vdisk = {}
    for name in 'pdisk', 'vdisk':
        d = eval(name)
        cmd = '%s storage %s controller=%s vdisk=%s' % \
              (binaries['omreport'], name, controller, vdisk_id)
        res = utils.execute(cmd)
        # Exit if we catch an error message
        if re.match(r'^Error:*', res[0]):
            msg = ("Error: Unable to get drive info for vdisk %s\n"
                   "Omreport error: %s") % (vdisk_id, res[0])
            utils.exit(msg)
        else:
            # The perc controller is attached to a slot and we need to know
            # its id otherwise is pointless to go any further
            try:
                d['slot'] = re.findall(r'Slot \d', res[1])[0][-1]
            except:
                msg = ("Error: can't fetch the slot number.\n"
                       "Probably the drive has been removed already.\n"
                       "Controller: %s, vdisk: %s") % (controller,
                                                      vdisk_id)
                utils.exit(msg)

            # We can split everything after the second element by ':'
            # so we will have a very nice dictionary (with 0 effort)
            for e in res[2:]:
                k, v = e.split(':', 1)
                d[k.lower().strip()] = v.lower().strip()
            results['%s_status' % name] = d['status']
        name = d

    results['port'] = pdisk['id']
    results['serial'] = pdisk['serial no.']
    results['model'] = pdisk['product id']
    results['firmware'] = pdisk['revision']
    results['slot'] = pdisk['slot']
    capacity = pdisk['capacity'].split()[0].split('.')[0]
    results['capacity'] = capacity.replace(',', '.')[:4] + ' TB'
    return results


def remove_device(controller, vdisk_id, pdisk_id):
    # TODO: Check on device xfs errors and bad mount. mtab
    """
    Remove a device from the controller given a specific port. Turns the
    indicator light on for the port and, if everything goes well, it will go
    ahead and attempt to have the device removed.

    :param controller: The controller id.
    :param vdisk_id: The id of the vdisk to remove.
    :param pdisk_id: The id of the pdisk to remove.
    :returns: A boolean value that reflects the result of the operation.
    """
    controller = str(controller)
    vdisk_id = str(vdisk_id)
    # First try to turn the indicator light on for the device port
    indicator_cmd = '%s storage pdisk action=blink controller=%s pdisk=%s' \
        % (binaries['omconfig'], controller, pdisk_id)
    indicator_result = utils.execute(indicator_cmd)
    if not 'Command successful!' in indicator_result[0]:
        msg = ("Failed to turn the indicator light on for pdisk %s. "
               "Removal of device on controller %s failed.\n"
               "Omconfig error: %s ") % (pdisk_id, controller,
                                         indicator_result[0])
        utils.exit(msg)

    # If all goes well then proceed with removing the device unit
    removal_cmd = ('%s storage vdisk action=deletevdisk controller=%s '
                   'vdisk=%s' % (binaries['omconfig'], controller, vdisk_id))
    removal_result = utils.execute(removal_cmd)
    if not 'Command successful!' in removal_result[0]:
        msg = ("Error: Failed to remove vdisk %s from "
               "controller %s for pdisk %s\n"
               "Omconfig error: %s ") % (vdisk_id, controller,
                                         pdisk_id, removal_result[0])
        utils.exit(msg)
    return True


def add_device(controller, vdisk_id, pdisk_id=None, format=True):
    """
    Add a device back into the system.

    :param controller: The controller id.
    :param vdisk_id: The id of the vdisk to add.
    :param pdisk_id: The id of the pdisk to add. If left to None we will need
                     to fetch its value from the backend.
    :returns: A boolean value that reflects the result of the operation.
    """
    controller = str(controller)
    vdisk_id = str(vdisk_id)
    device_path = '/dev/c%su%sp' & (controller, vdisk_id)
    drive_info = get_drive_info(controller, vdisk_id)

    # Should check if there is a replace operation in progress. TODO
    # Should also allow --force to override. TODO

    # Sometimes after a drive has been swapped the vdisk is recreated right
    # away. We need to check this and clean up if necessary.
    if drive_info['vdisk_status']:  # TOCHECK
        remove_device(controller, vdisk_id)

    # Now that we cleaned up the vdisk we can move on and create the new one
    add_cmd = '%s storage controller action=createvdisk controller=%s ' \
        'pdisk=%s raid=r0 size=max stripesize=64kb diskcachepolicy=disabled ' \
        'readpolicy=ara writepolicy=wb' % \
        (binaries['omconfig'], controller, device['port'])
    add_result = utils.execute(add_cmd)
    if not 'Command successful!' in add_result[0]:
        msg = ("Cannot add disk number %s on controller %s.\n"
               "Error: %s ") % (device['port'], controller, str(add_result))
        utils.exit(msg)

    """
    Device added, so partition and format it
    """
    if format:
        utils.format_drive(device_path, '3T')
    """
    Now let's mount the device back into the system
    """
    utils.add_mountpoint()
    """
    Let's go ahead and turn the indicator light off
    """
    indicator_cmd = '%s storage pdisk action=unblink controller=%s pdisk=%s' \
        % (binaries['omconfig'], controller, device['port'])
    indicator_result = utils.execute(indicator_cmd)
    if not 'Command successful!' in indicator_result[0]:
        msg = ("Error: Failed to turn the indicator light off "
               "for pdisk %s on controller %s.\n"
               "Error: %s ") % (device['port'], controller,
                                indicator_result[0])
        utils.exit(msg)
    return True
