# for can_recv_app.py
# this is the code that only interacts with the database

import sqlite3
import pkg_resources, os

# Add queries separately so it's easier to change later on

GET_ALL_DATA = "SELECT * FROM can_test_db;"

def connect():
    # open data file. if not there, create one
    # os and pathlib are used to create the db file in the same location every
    # time.
    db_file = pkg_resources.resource_filename(
        __name__,
        os.path.join(os.pardir, 'resources', 'TEST.db'))
    return sqlite3.connect(db_file, 
                           isolation_level=None, 
                           check_same_thread=False)

def create_tables(connection, tablename, columns):
    #context manager, when we create database, it gets saved to the ^^ file

    #create a string of question marks depending on # of column values
    columns = "(timestamp REAL,\n" \
              + ",\n".join(f"{k} {'REAL' if v.is_averaged else 'INT'}" for k, v in columns) \
              + ")"

    CREATE_CAN_TABLE = f"""CREATE TABLE IF NOT EXISTS {tablename}\n {columns}"""

    # not global anymore - the tablename and such 
    with connection:
        connection.execute(CREATE_CAN_TABLE)


def add_row(connection, r_timestamp, r_values, r_name):
    qmarks = f"(?, " + ", ".join("?" for _ in r_values) + ")"
    vals = [r_timestamp] + [v.value for v in r_values]
    insert_row = f"INSERT INTO {r_name} VALUES\n" + qmarks

    with connection:
        connection.execute(insert_row, vals) # 2nd param has to be tuple


def get_all_data(connection):
    with connection:
        return connection.execute(GET_ALL_DATA).fetchall()
