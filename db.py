import sqlite3

def get_db_connection():
    connection = sqlite3.connect("database.db")
    return connection

def set_up_db():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY,
            type INTEGER NOT NULL,
            season TEXT NOT NULL,
            division TEXT NOT NULL,
            team INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            battletag TEXT NOT NULL,
            team INTEGER,
        )
    ''')
    connection.commit()
    connection.close()