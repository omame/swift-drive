import sqlite3
from swift_drive.common.config import get_config


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class Backend():
    def __init__(self):
        # Define the accepted statuses for the ports and drives
        self.valid_port_status_list = ['active', 'error', 'disabled',
                                       'unknown', 'foreign']
        self.valid_drive_status_list = ['active', 'failed', 'missing',
                                        'disabled', 'unknown']
        self.conf = get_config('sqlite')
        dbfile = self.conf['sqlite_db']
        self.db = sqlite3.connect(dbfile)
        self.db.row_factory = dict_factory
        self.cur = self.db.cursor()

    def init_schema(self):
        """
        Initialise the SQLite db schema.
        WARNING: it will wipe out all the existing data!
        """
        query = 'DROP TABLE IF EXISTS drives'
        self.cur.execute(query)
        query = '''
        CREATE TABLE drives (
            name INT,
            serial TEXT,
            last_update INT,
            model TEXT,
            firmware TEXT,
            capacity TEXT,
            status TEXT,
            PRIMARY KEY (name, serial)
        )

        '''
        self.cur.execute(query)
        self.db.commit()

        query = 'DROP TABLE IF EXISTS ports'
        self.cur.execute(query)
        query = '''
        CREATE TABLE ports (
            name TEXT,
            controller_id TEXT,
            drive_serial TEXT,
            status INT,
            PRIMARY KEY (name, controller_id)
        )

        '''
        self.cur.execute(query)
        self.db.commit()

        query = 'DROP TABLE IF EXISTS controllers'
        self.cur.execute(query)
        query = '''
        CREATE TABLE controllers (
            id TEXT PRIMARY KEY,
            slot INT
        )
        '''
        self.cur.execute(query)
        self.db.commit()

        query = 'DROP TABLE IF EXISTS events'
        self.cur.execute(query)
        query = '''
        CREATE TABLE events (
            time INT,
            drive_serial TEXT,
            error TEXT,
            status INT,
            notification_sent INT
        )
        '''
        self.cur.execute(query)
        self.db.commit()

        query = 'DROP TABLE IF EXISTS tickets'
        self.cur.execute(query)
        query = '''
        CREATE TABLE tickets (
            time INT,
            ticket_number TEXT PRIMARY KEY,
            drive_serial TEXT,
            status INT
        )

        '''
        self.cur.execute(query)
        self.db.commit()

    # Drive related methods

    def add_drive(self, name, serial, last_update, model,
                  firmware, capacity, status):
        """
        Adds a drive to the drives table.

        :param name: The device name.
        :param serial: The drive serial number.
        :param last_update: The time when the drive is being added.
        :param model: The drive model.
        :param firmware: The drive firmware version.
        :param capacity: The drive capacity.
        :param status: The status of the drive. Accepted values: 'online',
                       'failed', 'missing', 'disabled' and 'unknown'.
        """
        if status not in self.valid_drive_status_list:
            raise Exception('Invalid drive status')
        query = '''
        INSERT INTO drives (
            name,
            serial,
            last_update,
            model,
            firmware,
            capacity,
            status
        ) VALUES(?, ?, ?, ?, ?, ?, ?)

        '''
        self.cur.execute(query, (name, serial, last_update, model,
                                 firmware, capacity, status))
        self.db.commit()

    def delete_drive(self, name, serial):
        """
        Deletes a drive entry from the drives table.
        This shouldn't be used normally as we're looking to keep track of
        the device history, so we can even detect when a failed drive has been
        recycled.

        :param name: The device name.
        :param serial: The drive serial number.

        """
        query = 'DELETE FROM drives WHERE name = ? and serial = ?'
        self.cur.execute(query, (name, serial))
        self.db.commit()

    def update_drive(self, name, serial, **kwargs):
        """
        Updates drives information.

        :param name: The time when the drive is being added.
        :param serial: The drive serial number. Accepted values: 'online',
                       'failed', 'missing', 'disabled' and 'unknown'.
        """
        for field, value in kwargs.items():
            if field == 'status' and field not in self.valid_drive_status_list:
                raise Exception('Invalid drive status')
            query = 'UPDATE drives SET %s = ? where name = ? and serial = ?' %\
                    field
            self.cur.execute(query, (field, name, serial))
            self.db.commit()

    def get_drive(self, name):
        """
        Extract drive information.
        This looks for the most updated entry.

        :param name: The device name.
        :returns: A dictionary with the information.
        """
        query = 'SELECT * FROM drives WHERE name = ? ORDER BY last_update DESC'
        self.cur.execute(query, (name, ))
        drive = self.cur.fetchone()
        if not drive:
            return None
        return drive

    # port related methods

    def add_port(self, name, controller_id, drive_serial, status):
        """
        Adds a port to the ports table.

        :param name: The port name.
        :param controller_id: The id of the controller where the port is
                              attached.
        :param drive_serial: The serial of the drive currently connected to
                             the port.
        :param status: The status of the port. Accepted values: active, error
                       or unknown.
        """
        if status not in self.valid_port_status_list:
            raise Exception('Invalid port status')
        query = '''
        INSERT INTO ports (
            name,
            controller_id,
            drive_serial,
            status
        ) VALUES (?, ?, ?, ?)
        '''
        self.cur.execute(query, (name, controller_id, drive_serial, status))
        self.db.commit()

    def delete_port(self, name, controller_id):
        """
        Removes a port from the ports table.

        :param name: The port name.
        :param controller_id: The id of the controller where the port is
                              attached.
        """
        query = 'DELETE FROM ports WHERE name = ? and controller_id = ?'
        self.cur.execute(query, (name, controller_id))
        self.db.commit()

    def update_port(self, name, controller_id, **kwargs):
        """
        Updates information for a port.

        :param name: The port name.
        :param controller_id: The id of the controller where the port is
                              attached.
        """
        for field, value in kwargs.items():
            if field == 'status' and field not in self.valid_port_status_list:
                raise Exception('Invalid port status')
            query = '''
            UPDATE ports SET %s = ?
            WHERE name = ?
            AND controller_id = ?
            ''' % field
            self.cur.execute(query, (value, name, controller_id))
            self.db.commit()

    def get_port(self, name, controller_id):
        """
        Extract port information.

        :param name: The port name.
        :param controller_id: The id of the controller where the port is
                              attached.
        :returns: A dictionary with the information.
        """
        query = 'SELECT * FROM ports WHERE name = ? and controller_id = ?'
        self.cur.execute(query, (name, controller_id))
        res = self.cur.fetchone()
        return res

    # Controller related methods

    def add_controller(self, controller_id, slot):
        """
        Adds a controller to the controllers table.

        :param controller_id: The id of the controller.
        :param slot: The PCI slot where the controller is connected.
        """
        query = '''
        INSERT INTO controllers (
            id,
            slot
        ) VALUES (?, ?)
        '''
        self.cur.execute(query, (controller_id, slot))
        self.db.commit()

    def delete_controller(self, controller_id):
        """
        Removes a controller from the controllers table.

        :param controller_id: The id of the controller.
        """
        query = 'DELETE FROM controllers WHERE id = ?'
        self.cur.execute(query, (controller_id,))
        self.db.commit()

    def update_controller_id(self, slot, controller_id):
        """
        Update the controller id. This is particularly useful with
        LSI controllers as the id tends to change after every reboot.

        :param slot: The PCI slot where the controller is connected.
        :param controller_id: The new id of the controller.
        """
        query = 'UPDATE controllers SET id = ? WHERE slot = ?'
        self.cur.execute(query, (controller_id, slot))
        self.db.commit()

    def get_controller_slot(self, controller_id):
        """
        Returns the PCI slot for the given controller id.

        :param controller_id: the id of the controller
        :returns: the slot number for the controller
        """
        query = 'SELECT slot FROM controllers WHERE id = ?'
        self.cur.execute(query, (controller_id,))
        try:
            return self.cur.fetchone()['port']
        except:
            return None

    def get_controller_id(self, drive_serial):
        """
        Get the controller id for a given drive serial.

        :param drive_serial: The serial number of the drive.
        :returns: The controller id.
        """
        query = '''
        SELECT controller_id FROM ports
        WHERE drive_serial = ?
        AND status = 'active'
        '''
        self.cur.execute(query, (drive_serial, ))
        try:
            return self.cur.fetchone()['controller_id']
        except:
            return None

    # Event related methods

    def add_event(self, time, drive_serial, error, status, notification_sent):
        """
        Adds an event to the events table.

        :param time: The time when the event happened.
        :param drive_serial: The drive's serial number.
        :param error: The error reported by the controller.
        :param status: The event status. Could be new, inprogress, closed and
                       error.
        :param notification_sent: Should be 'yes' if a notification has been
                                  sent.

        """
        if notification_sent not in [0, 1]:
            raise Exception('Invalid notification_sent status')
        query = '''
        INSERT INTO events (
            time,
            drive_serial,
            error,
            status,
            notification_sent
        ) VALUES (?, ?, ?, ?, ?)
        '''
        self.cur.execute(query, (time, drive_serial, error,
                                 status, notification_sent))
        self.db.commit()

    def delete_event(self):
        """
        Do you really need this?
        """
        pass

    def update_event(self, time, drive_serial, **kwargs):
        """
        Updates information for an existing event.

        :param time: The time when the event happened.
        :param drive_serial: The drive's serial number.
        """
        for field, value in kwargs.items():
            if field == 'notification_sent' and value not in [0, 1]:
                raise Exception('Invalid notification_sent status')
            query = '''
            UPDATE events SET %s = ?
            WHERE time = ?
            AND drive_serial = ?
            ''' % field
            self.cur.execute(query, (value, time, drive_serial))
            self.db.commit()

    def get_event(self, drive_serial, **kwargs):
        """
        Extract event information.
        NOTE: If the keyword time is present, it represents the starting time
        for the search.

        :param drive_serial: The drive's serial number.
        :returns: A list of dictionaries containing the information.
        """
        query = 'SELECT * FROM events WHERE drive_serial = ?'
        values = [drive_serial]
        for field, value in kwargs.items():
            if field == 'time':
                query += ' AND time > ?'
            else:
                query += ' AND %s = ?' % field
            values.append(value)
        self.cur.execute(query, tuple(values))
        res = self.cur.fetchall()
        return res

    # Ticket related methods

    def add_ticket(self, time, ticket_number, drive_serial, status):
        """
        Adds a ticket to the tickets table.

        :param time: The time when the event happened.
        :param ticket_number: The ticket number.
        :param drive_serial: The drive's serial number.
        :param status: The event status. Could be new, inprogress, closed and
                       error.
        """
        query = '''
        INSERT INTO tickets (
            time,
            ticket_number,
            drive_serial,
            status
        ) VALUES (?, ?, ?, ?)
        '''
        self.cur.execute(query, (time, ticket_number, drive_serial, status))
        self.db.commit()

    def delete_ticket(self):
        """
        Do you really need this?
        """
        pass

    def update_ticket(self, ticket_number, **kwargs):
        """
        Updates information for an existing ticket.

        :param time: The time when the event happened.
        :param ticket_number: The ticket number.
        """
        for field, value in kwargs.items():
            query = '''
            UPDATE tickets SET %s = ?
            WHERE ticket_number = ?
            ''' % field
            self.cur.execute(query, (value, ticket_number))
            self.db.commit()

    def get_ticket(self, ticket_number):
        """
        Extract ticket information.

        :param ticket_number: The ticket number.
        :returns: A dictionary with the information.
        """
        query = 'SELECT * FROM tickets WHERE ticket_number = ?'
        self.cur.execute(query, (ticket_number,))
        res = self.cur.fetchone()
        return res
