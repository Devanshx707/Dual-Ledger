"""Database setup. Creates the tables and returns a connection and cursor."""
import sqlite3 as sql

from config import DB_NAME


def connect_db(path=DB_NAME):
    conn = sql.connect(path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personal_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL, amount REAL NOT NULL, date TEXT NOT NULL)""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL, payer TEXT NOT NULL, amount REAL NOT NULL,
            category TEXT NOT NULL, date TEXT NOT NULL, participants TEXT NOT NULL)""")
    conn.commit()
    return conn, cursor
