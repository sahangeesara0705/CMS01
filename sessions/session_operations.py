import psycopg2
import os
import uuid
import cms_utils.uuid
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler

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
        CREATE TABLE IF NOT EXISTS "User" (
            id SERIAL PRIMARY KEY,
            user_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            profile_image_url TEXT,
            sign_in_type TEXT NOT NULL,
            access_token TEXT NOT NULL,
            access_token_secret TEXT
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS Session (
            id SERIAL PRIMARY KEY,
            session_id UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
            user_id INTEGER REFERENCES "User"(id) ON DELETE CASCADE,
            ip_address TEXT,
            fingerprint_hash TEXT
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def get_session_from_cookies(cookie_header):
    if cookie_header:
        cookie = SimpleCookie()
        cookie.load(cookie_header)
        return cookie.get("session_id").value if "session_id" in cookie else None
    else:
        return None

def set_session(user_id, ip_address, fingerprint_hash):
    session_id = str(uuid.uuid4())

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO Session (session_id, user_id, ip_address, fingerprint_hash)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (session_id) DO UPDATE SET
        ip_address = EXCLUDED.ip_address,
        fingerprint_hash = EXCLUDED.fingerprint_hash;
    ''', (session_id, user_id, ip_address, fingerprint_hash))
    conn.commit()
    cur.close()
    conn.close()

    cookie = SimpleCookie()
    cookie["session_id"] = session_id
    cookie["session_id"]["path"] = "/"
    cookie["session_id"]["httponly"] = True
    return cookie

def set_user(user_id, name, email, password_hash, profile_image_url, sign_in_type, access_token, access_token_secret):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM "User" WHERE email = %s', (email,))
    if cur.fetchone():
        return None
    cur.execute('''
        INSERT INTO "User" (user_id, name, email, password_hash, profile_image_url, sign_in_type, access_token, access_token_secret)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            name = EXCLUDED.name,
            email = EXCLUDED.email,
            password_hash = EXCLUDED.password_hash,
            profile_image_url = EXCLUDED.profile_image_url,
            sign_in_type = EXCLUDED.sign_in_type,
            access_token = EXCLUDED.access_token,
            access_token_secret = EXCLUDED.access_token_secret
    ''', (user_id, name, email, password_hash, profile_image_url, sign_in_type, access_token, access_token_secret))

    # cur.execute('''
    #         INSERT INTO "User" (user_id, name, profile_image_url, sign_in_type, access_token, access_token_secret)
    #         VALUES (%s, %s, %s, %s, %s, %s)
    #     ''', (user_id, name, profile_image_url, sign_in_type, access_token, access_token_secret))
    conn.commit()
    cur.close()
    conn.close()

    cookie = SimpleCookie()
    cookie["sign_in_type"] = sign_in_type
    cookie["sign_in_type"]["path"] = "/"
    cookie["sign_in_type"]["httponly"] = True
    return cookie

def get_session(session_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Session WHERE session_id = %s", (session_id,))
    session = cur.fetchone()
    cur.close()
    conn.close()
    return session

def get_user_by_session_id(session_id):
    if not cms_utils.uuid.is_valid_uuid(session_id):
        return None

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT "User".* FROM "User"
        JOIN Session ON "User".id = Session.user_id
        WHERE Session.session_id = %s
    ''', (session_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def get_user_by_user_id(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT * FROM "User" WHERE user_id = %s
    ''', (str(user_id),))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def get_user_by_email_and_password(email, password_hash):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT user_id, name, profile_image_url FROM "User" WHERE email= %s AND password_hash = %s', (email, password_hash))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return None
    return user

setup_database()