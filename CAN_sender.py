from typing import cast
from time import sleep
from threading import Thread, Lock
from pathlib import Path
from copy import deepcopy

import can
import cantools.database
from cantools.database.can.database import Database
from cantools.typechecking import SignalDictType
from digi.xbee.devices import XBeeDevice

from definitions import PROJECT_ROOT, BUFFERED_XBEE_MSG_END
from row import Row
from util import add_dbc_file
import serial

VIRTUAL_BUS_NAME = "virtbus"

XBEE_PORT = "COM6"
XBEE_BAUD_RATE = 9600
REMOTE_NODE_ID = "Node"

SERIAL_PORT = "COM9"
SERIAL_BAUD_RATE = 500000

xbee = XBeeDevice(XBEE_PORT, XBEE_BAUD_RATE)
xbee.open()

remote = xbee.get_network().discover_device(REMOTE_NODE_ID)
assert remote is not None

# Thread communication globals
row_lock = Lock()

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(Path(PROJECT_ROOT).joinpath("resources", "mppt.dbc")))
#add_dbc_file(db, Path(PROJECT_ROOT).joinpath("resources", "motor_controller.dbc"))

# The rows that will be added to the database
rows = [Row(db, node.name) for node in db.nodes]

def get_packets(interface) -> iter:
    """Generates CAN Packets."""
    if interface == 'canusb':
        with serial.Serial(SERIAL_PORT, SERIAL_BAUD_RATE) as receiver:
            while(True):
                raw = receiver.read_until(b';').decode()
                if len(raw) != 23: continue
                raw = raw[1:len(raw) - 1]
                raw = raw.replace('S', '')
                raw = raw.replace('N', '')
                tag = int(raw[0:3], 16)
                data = bytearray.fromhex(raw[3:])
                sleep(.1)
                yield can.Message(arbitration_id=tag, data=data)
    elif interface == 'pican':
        with can.interface.Bus(channel='can0', bustype='socketcan') as bus:
            for msg in bus:
                tag = msg.arbitration_id
                data = msg.data
                yield can.Message(arbitration_id=tag, data=data)
    else:
        raise Exception('Invalid interface')

def row_accumulator_worker(bus: can.ThreadSafeBus):
    """
    Observes messages sent on the `bus` and accumulates them in a global row.
    """
    for msg in get_packets("canusb"):
        assert msg is not None
        i = next(i for i, r in enumerate(rows) if r.owns(msg, db))
        decoded = cast(SignalDictType, db.decode_message(msg.arbitration_id, msg.data))
        with row_lock:
            for k, v in decoded.items():
                rows[i].signals[k].update(v)

def buffered_payload(payload: str, chunk_size: int = 256, terminator: str = BUFFERED_XBEE_MSG_END) -> list[str]:
        payload += terminator
        return [payload[i:i + chunk_size] for i in range(0, len(payload), chunk_size)]

def sender_worker():
    """
    Serializes rows into the queue.
    """
    while True:
        sleep(2.0)
        with row_lock:
            copied = deepcopy(rows)
        for row in copied:
            row.stamp()
            for chunk in buffered_payload(row.serialize()):
                print(chunk, "\n")
                xbee.send_data(remote, chunk)
                #xbee.send_data(remote, row.serialize()) #only call serialize once, it clears the val


if __name__ == "__main__":
    # Create a thread to read off the bus and maintain the rows
    accumulator = Thread(target=row_accumulator_worker,
                         args=(can.ThreadSafeBus(VIRTUAL_BUS_NAME, bustype='virtual'),),
                         daemon=True)

    # Create a thread to serialize rows as would be necessary with XBees
    sender = Thread(target=sender_worker, daemon=True)

    accumulator.start()
    sender.start()

    sender.join()
