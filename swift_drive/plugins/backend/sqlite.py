import sqlite3
from swift_drive.common.config import get_config


class backend():
    def __init__(self):
        dbfile = get_config()['sqlite_db']
        self.db = sqlite3.connect(dbfile)
        self.cur = self.db.cursor()

    def init_schema(self):
        """
        Initialise the SQLite db schema.
        WARNING: it will wipe out all the existing data!
        """
        query = 'DROP TABLE IF EXISTS drives;'
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
        );

        '''
        self.cur.execute(query)
        self.db.commit()

        query = 'DROP TABLE IF EXISTS ports;'
        self.cur.execute(query)
        query = '''
        CREATE TABLE ports (
            name TEXT,
            controller_id TEXT,
            drive_serial TEXT,
            status INT,
            PRIMARY KEY (name, controller_id)
        );

        '''
        self.cur.execute(query)
        self.db.commit()

        query = 'DROP TABLE IF EXISTS controllers;'
        self.cur.execute(query)
        query = '''
        CREATE TABLE controllers (
            id TEXT PRIMARY KEY,
            slot INT
        );
        '''
        self.cur.execute(query)
        self.db.commit()

        query = 'DROP TABLE IF EXISTS events;'
        self.cur.execute(query)
        query = '''
        CREATE TABLE events (
            time INT,
            drive_serial TEXT,
            error TEXT,
            status INT,
            notification_sent INT
        );
        '''
        self.cur.execute(query)
        self.db.commit()

        query = 'DROP TABLE IF EXISTS tickets;'
        self.cur.execute(query)
        query = '''
        CREATE TABLE tickets (
            time INT,
            ticket_number TEXT PRIMARY KEY,
            drive_serial TEXT,
            status INT
        );

        '''
        self.cur.execute(query)
        self.db.commit()

    def populate_schema(self):
        """
        """
        pass

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
        :param status: The status of the drive.
        """
        query = '''
        INSERT INTO drives (
            name,
            serial,
            last_update,
            model,
            firmware,
            capacity,
            status
        ) VALUES(?, ?, ?, ?, ?, ?, ?);

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

        :param serial: The drive serial number.

        """
        query = 'DELETE FROM drives WHERE name = ? and serial = ?;'
        self.cur.execute(query, (name, serial))
        self.db.commit()

    def update_drive(self, name, serial, **kwargs):
        """
        Updates drives information.

        :param last_update: The time when the drive is being added.
        :param serial: The drive serial number.
        :param model: The drive model.
        :param firmware: The drive firmware version.
        :param capacity: The drive capacity.
        :param status: The status of the drive.
        """
        for field, value in kwargs.items():
            query = 'UPDATE drives SET ? = ? where name = ? and serial = ?;'
            self.cur.execute(query, (field, value, name, serial))
            self.db.commit()

    def get_drive(self, name, serial):
        """
        """
        pass

    # Port related methods

    def add_port(self, name, controller_id, drive_serial, status):
        """
        """
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
        """
        query = 'DELETE FROM ports WHERE name = ? and controller_id = ?;'
        self.cur.execute(query, (name, controller_id))
        self.db.commit()

    def update_port(self, name, controller_id, **kwargs):
        """
        """
        for field, value in kwargs.items():
            query = 'UPDATE ports SET ? = ? where name = ? and controller_id = ?;'
            self.cur.execute(query, (field, value, name, controller_id))
            self.db.commit()

    def get_port(self, name, controller_id):
        """
        """
        query = '''
                SELECT drive_serial, status
                FROM ports
                WHERE name = ? and controller_id = ?;
                '''
        self.cur.execute(query, (name, controller_id))
        slot = self.cur.fetchone()
        return slot

    # Controller related methods

    def add_controller(self, controller_id, slot):
        """
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
        """
        query = 'DELETE FROM controllers WHERE controller_id = ?;'
        self.cur.execute(query, (controller_id,))
        self.db.commit()

    def update_controller(self):
        """
        Do we really need this?
        """
        pass

    def get_controller(self, controller_id):
        """
        Returns the slot for the given controller id.

        :param controller_id: the id of the controller
        :returns: the slot number for the controller
        """
        query = 'SELECT slot FROM controllers WHERE id = ?;'
        self.cur.execute(query, (controller_id,))
        slot = self.cur.fetchone()[0]
        return slot

    # Event related methods

    def add_event(self, time, drive_serial, error, status, notification_sent):
        """
        """
        query = '''
        INSERT INTO events (
            time,
            drive_serial,
            error,
            status,
            notification_sent,
            PRIMARY KEY (time, drive_serial)
        ) VALUES (?, ?, ?, ?, ?)
        '''
        self.cur.execute(query, (time, drive_serial, error,
                                 status, notification_sent))
        self.db.commit()

    def delete_event(self):
        """
        Do we really need this?
        """
        pass

    def update_event(self, time, drive_serial, **kwargs):
        """
        """
        for field, value in kwargs.items():
            query = ('UPDATE events SET ? = ?',
                     ' where time = ? and drive_serial = ?;')
            self.cur.execute(query, (field, value, time, drive_serial))
            self.db.commit()

    # Ticket related methods

    def add_ticket(self, time, ticket_number, drive_serial, status):
        """
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
        Do we really need this?
        """
        pass

    def update_ticket(self, ticket_number, **kwargs):
        """
        """
        for field, value in kwargs.items():
            query = 'UPDATE tickets SET ? = ? where ticket_number = ?;'
            self.cur.execute(query, (field, value, ticket_number))
            self.db.commit()
