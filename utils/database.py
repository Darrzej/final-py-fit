import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv
from utils.auth import hash_password, verify_password

# Load environment variables
load_dotenv()
DB_PATH = os.getenv("DB_PATH", "data/fitai.db")

def get_connection():
    """Establishes a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        age INTEGER,
        height REAL,
        weight REAL,
        goal TEXT,
        frequency INTEGER
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        muscle_group TEXT,
        category TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        exercise_id INTEGER
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        exercise_id INTEGER,
        pr REAL,
        reps INTEGER,
        updated_at TEXT
    )""")
    conn.commit()
    conn.close()

def seed_exercises_from_csv():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM exercises")
    if cursor.fetchone()[0] == 0:
        try:
            df = pd.read_csv("data/exercises.csv")
            df.to_sql("exercises", conn, if_exists="append", index=False)
        except FileNotFoundError:
            print("Warning: exercises.csv not found. Skipping seed.")
    conn.close()

def add_user(username, password, age, height, weight, goal, frequency):
    conn = get_connection()
    cursor = conn.cursor()
    # SECURE: Hash the password before storing
    hashed = hash_password(password)
    try:
        cursor.execute("""
            INSERT INTO users (username, password, age, height, weight, goal, frequency)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, hashed, age, height, weight, goal, frequency))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    # SECURE: Verify the hashed password
    if user and verify_password(user[2], password):
        return user
    return None

def get_exercises():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM exercises", conn)
    conn.close()
    return df

def add_user_exercise(user_id, exercise_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_exercises (user_id, exercise_id) VALUES (?, ?)", (user_id, exercise_id))
    conn.commit()
    conn.close()

def get_user_exercises(user_id):
    conn = get_connection()
    query = """
        SELECT e.* FROM exercises e
        JOIN user_exercises ue ON e.id = ue.exercise_id
        WHERE ue.user_id = ?
    """
    df = pd.read_sql(query, conn, params=(user_id,))
    conn.close()
    return df

def update_stat(user_id, exercise_id, pr, reps, date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_stats (user_id, exercise_id, pr, reps, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, exercise_id, pr, reps, date))
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    conn = get_connection()
    query = """
        SELECT e.name, us.pr, us.reps, us.updated_at 
        FROM user_stats us
        JOIN exercises e ON us.exercise_id = e.id
        WHERE us.user_id = ?
        ORDER BY us.updated_at ASC
    """
    df = pd.read_sql(query, conn, params=(user_id,))
    conn.close()
    return df

def remove_user_exercise(user_id, exercise_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_exercises WHERE user_id = ? AND exercise_id = ?", (user_id, exercise_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_connection()
    df = pd.read_sql("SELECT id, username, age, height, weight, goal, frequency FROM users", conn)
    conn.close()
    return df

def delete_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_stats WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM user_exercises WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def export_database():
    conn = get_connection()
    users = pd.read_sql("SELECT * FROM users", conn)
    users.to_csv("data/users_export.csv", index=False)
    conn.close()
    return "Data exported to data/users_export.csv"