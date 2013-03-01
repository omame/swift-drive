import re
import shlex
import subprocess
from swift_drive.common import utils


binaries = ['omreport', 'omconfig']


def execute(cmd):
    """
    Formats the output of the perc800 controller command
    that is given back by the subprocess.

    :param cmd: The command that should be passed over to the subprocess call.
    :returns: An array with the line output.
    """
    if isinstance(cmd, unicode):
        cmd = cmd.encode('utf8')

    args = shlex.split(cmd)
    try:
        p = subprocess.Popen(args, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, close_fds=True)
    except:
        raise

    output = p.stdout.read()

    lines = []
    for x in output.strip().split('\n'):
        if not re.match(r'^$', x):
            lines.append(x)

    if len(lines) == 0:
        msg = ("Zero Error: command executed by format_sp_output funtion "
               "returned no lines.\n(Cmd: %s) ") % cmd
        lines.append(msg)

    return lines


def get_device_info(binary, controller, device):
    """
    Collects information about a device on provided controller & device

    :param binary: Location of the controller binaries.
    :param controller: The controller index.
    :param device: A dictionary with device details.
    :returns: A dictionary that contains an error code and also
              a message which could be an error message or another
              two dictionaries containing the collected results about
              the device.
    """

    results = {}
    pdisk = {}
    vdisk = {}
    for name in 'pdisk', 'vdisk':  # <-- BOOKMARK
        d = eval(name)
        cmd = '%s storage %s controller=%s vdisk=%s' % \
            (binary['omreport'], name, controller, device['unit'])
        res = execute(cmd)
        if re.match(r'^Error:*', res[0]):
            msg = ("Error: Unable to get drive info for device%s\n\t"
                   "Returned error, %s ") % (device['name'], res[0])
            results['message'] = msg
            results['code'] = 300
            return results
        else:
            # We'll use the slot to write the core ticket
            try:
                d['slot'] = re.findall(r'Slot \d', res[1])[0][-1]
            except:
                msg = ("Error: can't fetch the slot number.\n"
                        "Probably the drive has been removed already.\n\n"
                        "Controller: %s, unit: %s") % (controller,
                                                        device['unit'])
                results['message'] = msg
                results['code'] = 300
                return results

            # We can split everything after the second element by :
            # so we will have a very nice dictionary (with 0 effort)
            for e in res[2:]:
                k, v = e.split(':', 1)
                d[k.lower().strip()] = v.lower().strip()
        name = d

    # Set the global status for the drive
    if (pdisk['status'] != 'ok' or vdisk['status'] != 'ok'):
        results['status'] = 'failed'
    else:
        results['status'] = 'OK'
    results['port'] = pdisk['id']
    results['serial'] = pdisk['serial no.']
    results['model'] = pdisk['product id']
    results['firmware'] = pdisk['revision']
    results['slot'] = pdisk['slot']
    results['capacity'] = pdisk['capacity'].split()[0].split('.')[0].replace(',', '.')[:4] + ' TB'
    return results


def remove_device(binary, controller, device):
    """
    Starts the process to remove device from the controller
    port that is provided. Turns the indicator light for the
    port and if everything goes well there it will go ahead
    and attempt to have the device removed.

    TODO: Check on device xfs errors and bad mount. mtab

    :param binary: Location where the controller binary exists
    :param controller: The controller name/index
    :param device: A dictionary with device details

    :returns: A dictionary that includes an error code and message.
    """
    results = {'code': 0}

    """
    First try to turn the indicator light on for the device port
    """
    indicator_cmd = '%s storage pdisk action=blink controller=%s pdisk=%s' \
        % (binary['omconfig'], controller, device['port'])
    indicator_result = format_sp_output(indicator_cmd)
    if not 'Command successful!' in indicator_result[0]:
        results['code'] = 300
        msg = ("Error: Failed to turn the indicator light on for pdisk %s. "
               "Removal of device %s on controller %s failed (2) \n\t"
               "Returned error, %s ") % (device['port'], device['name'],
                                         controller, indicator_result[0])
        results['message'] = msg
        return results

    """
    If all goes well then proceed with removing the device unit
    """
    removal_cmd = '%s storage vdisk action=deletevdisk controller=%s vdisk=%s' \
        % (binary['omconfig'], controller, device['unit'])
    removal_result = format_sp_output(removal_cmd)
    if not 'Command successful!' in removal_result[0]:
        results['code'] = 300
        msg = ("Error: Failed to remove unit %s from controller %s "
               "for device %s and pdisk %s \n\t"
               "Returned error, %s ") % (device['unit'], controller,
                                         device['name'], device['port'],
                                         removal_result[0])
        results['message'] = msg
    else:
        results['message'] = removal_result[0]
    return results