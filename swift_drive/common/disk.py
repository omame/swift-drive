import os
import re
import subprocess
import urllib2
from swift_drive.common.utils import execute
try:
    from simplejson import json
except ImportError:
    import json


def get_unmounted_drives():
    """
    Get unmounted drives information from swift-recon

    :returns: A dictionary containing the unmounted drives
    """
    ip_address = '127.0.0.1'
    port = '6000'
    url = 'http://%s:%s/recon/unmounted' % (ip_address, port)

    retries = 0
    timeout = 10
    while (retries < 3):
        try:
            urlobj = urllib2.urlopen(url, timeout=timeout)
            break

        except urllib2.URLError, e:
            if str(e.reason) == 'timed out':
                retries = retries + 1
                timeout += 5

        except urllib2.HTTPError, e:
            print "Error code: %s" % e.code
            raise

    if retries == 3:
        exit(1)

    if re.match(r'^2[0-9][0-9]$', str(urlobj.code).strip()):
        body = urlobj.read()
        content = json.loads(body)

    return content


def is_mounted(device_name, basepath='/srv/node'):
    """
    Check if a device is mounted

    :param device_name: The name of the device to check. We assume that the
                        mount point has the same name.
    :param basepath: The path where swift drives are mounted.
    :returns: A boolean value that reflects the result of the operation.
    """
    return os.path.ismount(os.path.join(basepath, device_name))


def mount(device_name, basepath='/srv/node'):
    """
    Mount a drive back into the system. We assume that the filesystem is
    mounted using its label, so the line in /etc/fstab will start with LABEL=.
    Also, we assume that the label corresponds to the device name.

    :param device_name: The name of the device to mount. We assume that the
                        mount point has the same name.
    :param basepath: The path where swift drives are mounted.
    :returns: A boolean value that reflects the result of the operation.
    """
    mount_point = os.path.join(basepath, device_name)
    try:
        subprocess.call(['/bin/sed', '-i',
                         '"s/^#LABEL=%s/LABEL=%s/"' % (device_name, device_name),
                         '/etc/fstab'])
    except:
        msg = 'Failed uncomment /etc/fstab for device %s.' % device_name
        exit(msg)
    try:
        subprocess.call(['mount', mount_point])
    except:
        msg = 'Failed to mount device %s on mount point %s.' % \
              (device_name, mount_point)
        exit(msg)

    try:
        subprocess.call(['chown', 'swift.swift', mount_point])
    except:
        msg = 'Failed to change ownership on mount point %s.' % mount_point
        exit(msg)
    return True


def umount(device_name, basepath='/srv/node'):
    """
    Unmount a drive from the system.

    :param device_name: The name of the device to mount. We assume that the
                        mount point has the same name.
    :param basepath: The path where swift drives are mounted.
    :returns: A boolean value that reflects the result of the operation.
    """
    mount_point = os.path.join(basepath, device_name)
    try:
        subprocess.call(['umount', '-f', mount_point])
        return True
    except:
        msg = ("Mount point %s is still available and could not be "
               "unmounted" % mount_point)
        exit(msg)


def format_drive(device_path, size):
    '''
    Partition and format a drive in order to add it back to the syste.
    We assume that the partition label is identical to the device name and
    every drive even from different controllers share the same partition
    options. Maybe in the future this will become configurable.

    :param device_path: The path for the device to format (it's usually
                        something starting with /dev).
    :param size: The size for the partition in mkfs format (eg. 600G, 3T).
    :returns: A boolean value that reflects the result of the operation.
    '''
    # Check if the device exists before proceeding
    if os.path.exists(device_path):
        parted_label = '/sbin/parted -s ' + device_path + ' mklabel gpt'
        parted_result = execute(parted_label)
        if parted_result[0].startswith('Error:'):
            msg = ("Error: Unable to create GPT partition label for device %s"
                   "Parted error: %s ") % (device_path, parted_result[0])
            exit(msg)

        parted_part = '/sbin/parted -s %s mkpart primary xfs 0 %s' % \
                      (device_path, size)
        parted_result = execute(parted_part)
        if parted_result[0].startswith('Error:'):
            msg = ("Error: Unable to create partition table.\n"
                   "Parted error: %s") % (device_path, parted_result[0])
            exit(msg)
    else:
        msg = ("Error: Device %s does not seem to exist when attempting to "
               "Format the drive. Please check") % device_path
        exit(msg)

    # Now create filesystem on new partition
    partition_path = device_path + '1'
    mkfs_cmd = '/sbin/mkfs.xfs -i size=1024 -d su=64k,sw=1 -f -L %s %s' % \
        (device_path.split('/')[-1], partition_path)
    mkfs_result = execute(mkfs_cmd)
    if mkfs_result[0].startswith('Cannot'):
        msg = ("Cannot create a filesystem on device %s"
               "Mkfs error: %s") % (device_path, mkfs_result[0])
        exit(msg)
    return True
