import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv
from utils.auth import hash_password, verify_password

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "data/fitai.db")
CSV_DIR = "data/csv_backups/"

# Ensure the backup directory exists
if not os.path.exists(CSV_DIR):
    os.makedirs(CSV_DIR)

def get_connection():
    return sqlite3.connect(DB_PATH, timeout=20)

def _sync_to_csv(table_name):
    """Automatically exports the specified table to CSV."""
    try:
        conn = get_connection()
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        df.to_csv(f"{CSV_DIR}{table_name}.csv", index=False)
        conn.close()
    except Exception as e:
        print(f"Sync Error for {table_name}: {e}")

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
        frequency INTEGER,
        is_admin INTEGER DEFAULT 0
    )""")
    cursor.execute("CREATE TABLE IF NOT EXISTS exercises (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, muscle_group TEXT, category TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS user_exercises (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, exercise_id INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS user_stats (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, exercise_id INTEGER, pr REAL, reps INTEGER, updated_at TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS user_nutrition (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, calories INTEGER, protein INTEGER, date TEXT)")
    conn.commit()
    conn.close()
    # Initial sync
    for table in ['users', 'exercises', 'user_stats', 'user_nutrition']:
        _sync_to_csv(table)

def add_user(username, password, age, height, weight, goal, frequency, is_admin=0):
    conn = get_connection()
    cursor = conn.cursor()
    hashed = hash_password(password)
    try:
        cursor.execute("""
            INSERT INTO users (username, password, age, height, weight, goal, frequency, is_admin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, hashed, age, height, weight, goal, frequency, is_admin))
        conn.commit()
        _sync_to_csv('users') # AUTO-SYNC
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_stat(user_id, exercise_id, pr, reps, date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_stats (user_id, exercise_id, pr, reps, updated_at) VALUES (?, ?, ?, ?, ?)", (user_id, exercise_id, pr, reps, date))
    conn.commit()
    conn.close()
    _sync_to_csv('user_stats') # AUTO-SYNC

def add_nutrition_log(user_id, calories, protein, date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_nutrition (user_id, calories, protein, date) VALUES (?, ?, ?, ?)", (user_id, calories, protein, date))
    conn.commit()
    conn.close()
    _sync_to_csv('user_nutrition') # AUTO-SYNC

def promote_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    _sync_to_csv('users') # AUTO-SYNC

def delete_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    cursor.execute("DELETE FROM user_stats WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM user_nutrition WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    _sync_to_csv('users')
    _sync_to_csv('user_stats')
    _sync_to_csv('user_nutrition')

# Keep other GET functions same as before...
def get_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password, age, height, weight, goal, frequency, is_admin FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and verify_password(user[2], password): return user
    return None

def get_all_users():
    conn = get_connection()
    df = pd.read_sql("SELECT id, username, age, height, weight, goal, frequency, is_admin FROM users", conn)
    conn.close()
    return df

def get_user_stats(user_id):
    conn = get_connection()
    query = "SELECT e.name, us.pr, us.reps, us.updated_at FROM user_stats us JOIN exercises e ON us.exercise_id = e.id WHERE us.user_id = ? ORDER BY us.updated_at ASC"
    df = pd.read_sql(query, conn, params=(user_id,))
    conn.close()
    return df

def get_user_nutrition(user_id):
    conn = get_connection()
    query = "SELECT * FROM user_nutrition WHERE user_id = ? ORDER BY date DESC"
    df = pd.read_sql(query, conn, params=(user_id,))
    conn.close()
    return df

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
    query = "SELECT e.* FROM exercises e JOIN user_exercises ue ON e.id = ue.exercise_id WHERE ue.user_id = ?"
    df = pd.read_sql(query, conn, params=(user_id,))
    conn.close()
    return df

def remove_user_exercise(user_id, exercise_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_exercises WHERE user_id = ? AND exercise_id = ?", (user_id, exercise_id))
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
        except: pass
    conn.close()

def get_daily_nutrition_summary(user_id):
    conn = get_connection()
    # Aggregates nutrition by date in case of multiple entries per day
    query = """
        SELECT date, SUM(calories) as total_calories, SUM(protein) as total_protein 
        FROM user_nutrition 
        WHERE user_id = ? 
        GROUP BY date 
        ORDER BY date ASC
    """
    df = pd.read_sql(query, conn, params=(user_id,))
    conn.close()
    return df