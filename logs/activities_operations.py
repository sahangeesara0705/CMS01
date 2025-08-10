import psycopg2
import os
import uuid
import cms_utils.uuid
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler
from datetime import datetime

DB_NAME = "cms01"
DB_USER = "cms01"
DB_PASSWORD = "12345678cms01"
DB_HOST = "localhost"
DB_PORT = "5432"

def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def create_table():
    query = """
    CREATE TABLE IF NOT EXISTS activity (
        id SERIAL PRIMARY KEY,
        user_email VARCHAR(255) NOT NULL,
        activity_type VARCHAR(50) NOT NULL,
        activity TEXT NOT NULL,
        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()

def insert_activity(user_email, activity_type, activity):
    query = """
    INSERT INTO activity (user_email, activity_type, activity, time)
    VALUES (%s, %s, %s, %s)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, (user_email, activity_type, activity, datetime.now()))
    conn.commit()
    cur.close()
    conn.close()

def get_activities():
    query = "SELECT id, user_email, activity_type, activity, time FROM activity ORDER BY time DESC"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query)
    activities = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": row[0], "user_email": row[1], "activity_type": row[2], "activity": row[3], "time": row[4].isoformat()}
        for row in activities
    ]

if __name__ == "__main__":
    create_table()
    print("Table created successfully.")
    insert_activity("user@example.com", "login", "User logged in")
    print("Activity inserted.")