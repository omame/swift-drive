import os


def exit(msg, error_code=1):
    '''
    Exit with a specific error code (default 1).
    TODO: check if there is a notification module loaded and in case send out
          a message.

    :msg: Message to be returned
    :error_code: Exit code
    '''
    print msg
    exit(error_code)


def get_binaries(binaries):
    """
    Check if the binaries are executable. It understands if it should use the
    provided absolute path or look up the command in $PATH.
    Each module should know which binaries are required, so this function must
    remain generic.

    :param binaries: A list with the absolute path or just the names for the
                     binaries.
    :returns: A dictionary with the binary paths that actually exist
                     on the system. If the binary isn't found or isn't
                     executable the value will be a boolean False.
                     Format: {binary: binarypath}
    """
    def is_exe(binarypath):
        return os.path.isfile(binarypath) and os.access(binarypath, os.X_OK)

    results = {}
    for binary in binaries:
        binary_name = binary.split('/')[-1]
        results[binary_name] = False
        # If there's a directory separator then assume it's an absolute path
        if '/' in binary:
            if is_exe(binary):
                results[binary_name] = binary
        else:
            # Otherwise we need to search for the binary in $PATH
            binary_name = binary
            for path in os.environ['PATH'].split(os.pathsep):
                path = path.strip('"')
                binary_path = os.path.join(path, binary_name)
                if is_exe(binary_path):
                    results[binary] = binary_path
    return results


def check_mountpoint(device_name, basepath='/srv/node'):
    """
    Check if a device is mounted

    :param device_name: The name of the device to check. We assume that the
                        mount point has the same name.
    :param basepath: The path where swift drives are mounted.
    :returns: A boolean that tells is the device is mounted or not.
    """

    return os.path.ismount(os.path.join(basepath, device_name))


def add_mountpoint(device):
    pass
