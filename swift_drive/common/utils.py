import os
import re
import shlex
import socket
import subprocess
from swift_drive.plugins.notification import *
from swift_drive.common.config import get_config


def get_hostname():
    return socket.gethostname()


def execute(cmd):
    """
    execute a command and formats the output that is given back by
    the subprocess.

    :param cmd: The command that should be passed over to the subprocess call.
    :returns: An array with the line output.
    """
    if isinstance(cmd, unicode):
        cmd = cmd.encode('utf8')

    args = shlex.split(cmd)
    try:
        p = subprocess.Popen(args,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             close_fds=True)
    except:
        raise

    output = p.stdout.read()

    lines = []
    for x in output.strip().split('\n'):
        if not re.match(r'^$', x):
            lines.append(x)

    if len(lines) == 0:
        msg = ("Zero Error: command returned no lines.\n(Cmd: %s) ") % cmd
        lines.append(msg)

    return lines


def exit(message, subject='', error_code=1):
    '''
    Exit with a specific error code (default 1).
    TODO: check if there is a notification module loaded and in case send out
          a message.

    :msg: Message to be returned
    :error_code: Exit code
    '''
    try:
        notification_types = get_config()['notifications'].split(',')
        for notification in notification_types:
            # try:
            eval(notification).send_notification(subject, message)
            # except:
                # raise Exception('Error: notification type not found')
    except:
        # Nothing serious, just no need to notify
        pass
    print message
    # sys.exit(error_code)


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
