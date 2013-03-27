from swift_drive.common.config import get_config


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
        pass

        # Fetch all the information from the controller
        pass

        # Populate the backend with the information we just collected
        pass


def main():
    """
    Main entry point to the init; just calls `init().main()`.
    """
    return Init().main()
