import sqlite3

def get_connection():
    conn = sqlite3.connect("data/workouts.db")
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            exercise TEXT,
            sets INTEGER,
            reps INTEGER,
            weight REAL
        )
    """)
    conn.commit()
    conn.close()

def add_workout(date, exercise, sets, reps, weight):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO workouts (date, exercise, sets, reps, weight)
        VALUES (?, ?, ?, ?, ?)
    """, (date, exercise, sets, reps, weight))
    conn.commit()
    conn.close()

def get_all_workouts():
    conn = get_connection()
    df = None
    try:
        import pandas as pd
        df = pd.read_sql_query("SELECT * FROM workouts", conn)
    except Exception as e:
        print("Error reading workouts:", e)
    conn.close()
    return df
