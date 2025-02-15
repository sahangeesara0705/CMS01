import psycopg2
import os
from http.cookies import SimpleCookie

DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "abc"
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

def setup_database():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            user_id TEXT UNIQUE NOT NULL,
            access_token TEXT NOT NULL,
            screen_name TEXT NOT NULL,
            name TEXT NOT NULL,
            profile_image_url TEXT NOT NULL
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

def get_session_from_cookies(cookie_header):
    cookie = SimpleCookie()
    cookie.load(cookie_header)
    return cookie.get("session_id").value if "session_id" in cookie else None

def set_session(user_id, access_token, access_token_secret, screen_name, name, profile_image_url):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO sessions (user_id, access_token, access_token_secret, screen_name, name, profile_image_url)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
        access_token = EXCLUDED.access_token
        access_token_secret = EXCLUDED.access_token_secret,
        screen_name = EXCLUDED.screen_name,
        name = EXCLUDED.name,
        profile_image_url = EXCLUDED.profile_image_url;
    ''', (user_id, access_token, access_token_secret, screen_name, name, profile_image_url))
    conn.commit()
    cur.close()
    conn.close()

def get_session(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sessions WHERE user_id = %s", {user_id})
    session = cur.fetchone()
    cur.close()
    conn.close()
    return session

setup_database()