import sqlite3

def get_db_connection():
    connection = sqlite3.connect("database.db")
    return connection

def set_up_db():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY,
            type INTEGER NOT NULL,
            division TEXT NOT NULL,
            season TEXT NOT NULL
        )
    ''')
    connection.commit()
    connection.close()