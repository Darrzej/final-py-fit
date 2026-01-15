import sqlite3
import pandas as pd

DB_PATH = "data/fitai.db"

def get_connection():
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
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        muscle_group TEXT,
        category TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        exercise_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        exercise_id INTEGER,
        pr REAL,
        reps INTEGER,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()

def seed_exercises_from_csv():
    conn = get_connection()
    cursor = conn.cursor()

    df = pd.read_csv("data/exercises.csv")

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO exercises (name, muscle_group, category)
            SELECT ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM exercises WHERE name = ?
            )
        """, (row["name"], row["muscle_group"], row["category"], row["name"]))

    conn.commit()
    conn.close()

def get_exercises():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM exercises", conn)
    conn.close()
    return df

def add_user(username, password, age, height, weight, goal, frequency):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (username, password, age, height, weight, goal, frequency)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (username, password, age, height, weight, goal, frequency))
    conn.commit()
    conn.close()

def get_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users WHERE username = ? AND password = ?
    """, (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user_exercise(user_id, exercise_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_exercises (user_id, exercise_id)
        VALUES (?, ?)
    """, (user_id, exercise_id))
    conn.commit()
    conn.close()

def get_user_exercises(user_id):
    conn = get_connection()
    df = pd.read_sql(f"""
        SELECT e.* FROM exercises e
        JOIN user_exercises ue ON ue.exercise_id = e.id
        WHERE ue.user_id = {user_id}
    """, conn)
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
    df = pd.read_sql(f"""
        SELECT e.name, us.pr, us.reps, us.updated_at
        FROM user_stats us
        JOIN exercises e ON us.exercise_id = e.id
        WHERE us.user_id = {user_id}
        ORDER BY us.updated_at DESC
    """, conn)
    conn.close()
    return df

def user_has_exercise(user_id, exercise_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM user_exercises
        WHERE user_id = ? AND exercise_id = ?
    """, (user_id, exercise_id))
    exists = cursor.fetchone()
    conn.close()
    return exists is not None


def remove_user_exercise(user_id, exercise_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM user_exercises
        WHERE user_id = ? AND exercise_id = ?
    """, (user_id, exercise_id))
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
    exercises = pd.read_sql("SELECT * FROM exercises", conn)
    user_exercises = pd.read_sql("SELECT * FROM user_exercises", conn)
    user_stats = pd.read_sql("SELECT * FROM user_stats", conn)

    users.to_csv("backup_users.csv", index=False)
    exercises.to_csv("backup_exercises.csv", index=False)
    user_exercises.to_csv("backup_user_exercises.csv", index=False)
    user_stats.to_csv("backup_user_stats.csv", index=False)

    conn.close()

