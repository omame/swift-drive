from swift_drive.common.config import get_config
from swift_drive.common.utils import exit, confirm


class Init():
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

        # Load the ticketing module
        try:
            conf_backend = get_config()['backend']
            backend = getattr(__import__('swift_drive.plugins.backend',
                              fromlist=[conf_backend]), conf_backend)
            self.backend = backend.Backend()
        except:
            raise Exception('Failed to load %s backend module' % conf_backend)

    def main(self):
        # Wipe the current data in the backend
        msg = 'This will wipe out all the data in the backend! Are you sure?'
        if confirm(msg):
            self.backend.init()
        else:
            exit('OK, I am stopping here.')

        # Fetch all the information from the controllers and put them into the
        # backend
        controllers = self.controller.get_controllers()
        for controller_id in controllers:
            self.backend.add_controller(controller_id,
                                        controllers[controller_id])

        # For each controller get the list of the ports and put them into the
        # backend
        pass


def main():
    """
    Main entry point to the init; just calls `init().main()`.
    """
    return Init().main()
