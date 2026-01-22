import sqlite3
import pandas as pd
import os
from utils.auth import hash_password, verify_password

class DatabaseManager:
    def __init__(self, db_path="data/fitai.db"):
        self.db_path = db_path
        self.csv_dir = "data/csv_backups/"
        if not os.path.exists(self.csv_dir):
            os.makedirs(self.csv_dir)
        self.create_tables()

    def get_connection(self):
        return sqlite3.connect(self.db_path, timeout=20)

    def _sync_to_csv(self, table_name):
        """Internal method to mirror DB data to CSV."""
        try:
            with self.get_connection() as conn:
                df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
                df.to_csv(f"{self.csv_dir}{table_name}.csv", index=False)
        except Exception as e:
            print(f"Sync Error for {table_name}: {e}")

    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE, password TEXT, age INTEGER,
                height REAL, weight REAL, goal TEXT, frequency INTEGER, is_admin INTEGER DEFAULT 0
            )""")
            cursor.execute("CREATE TABLE IF NOT EXISTS exercises (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, muscle_group TEXT, category TEXT)")
            cursor.execute("CREATE TABLE IF NOT EXISTS user_exercises (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, exercise_id INTEGER)")
            cursor.execute("CREATE TABLE IF NOT EXISTS user_stats (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, exercise_id INTEGER, pr REAL, reps INTEGER, updated_at TEXT)")
            cursor.execute("CREATE TABLE IF NOT EXISTS user_nutrition (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, calories INTEGER, protein INTEGER, date TEXT)")
            conn.commit()
        # Initial sync for safety
        for t in ['users', 'exercises', 'user_stats', 'user_nutrition']: self._sync_to_csv(t)

    def add_user(self, username, password, age, height, weight, goal, frequency, is_admin=0):
        hashed = hash_password(password)
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO users (username, password, age, height, weight, goal, frequency, is_admin)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (username, hashed, age, height, weight, goal, frequency, is_admin))
                conn.commit()
            self._sync_to_csv('users')
            return True
        except sqlite3.IntegrityError: return False

    def get_user(self, username, password):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, password, age, height, weight, goal, frequency, is_admin FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user and verify_password(user[2], password): return user
        return None

    def get_all_users(self):
        with self.get_connection() as conn:
            return pd.read_sql("SELECT id, username, age, height, weight, goal, frequency, is_admin FROM users", conn)

    def update_stat(self, user_id, exercise_id, pr, reps, date):
        with self.get_connection() as conn:
            conn.execute("INSERT INTO user_stats (user_id, exercise_id, pr, reps, updated_at) VALUES (?, ?, ?, ?, ?)", (user_id, exercise_id, pr, reps, date))
            conn.commit()
        self._sync_to_csv('user_stats')

    def get_user_stats(self, user_id):
        with self.get_connection() as conn:
            query = "SELECT e.name, us.pr, us.reps, us.updated_at FROM user_stats us JOIN exercises e ON us.exercise_id = e.id WHERE us.user_id = ? ORDER BY us.updated_at ASC"
            return pd.read_sql(query, conn, params=(user_id,))

    def add_nutrition_log(self, user_id, calories, protein, date):
        with self.get_connection() as conn:
            conn.execute("INSERT INTO user_nutrition (user_id, calories, protein, date) VALUES (?, ?, ?, ?)", (user_id, calories, protein, date))
            conn.commit()
        self._sync_to_csv('user_nutrition')

    def get_daily_nutrition_summary(self, user_id):
        with self.get_connection() as conn:
            query = "SELECT date, SUM(calories) as total_calories, SUM(protein) as total_protein FROM user_nutrition WHERE user_id = ? GROUP BY date ORDER BY date ASC"
            return pd.read_sql(query, conn, params=(user_id,))

    def get_exercises(self):
        with self.get_connection() as conn: return pd.read_sql("SELECT * FROM exercises", conn)

    def add_user_exercise(self, user_id, exercise_id):
        with self.get_connection() as conn:
            conn.execute("INSERT INTO user_exercises (user_id, exercise_id) VALUES (?, ?)", (user_id, exercise_id))
            conn.commit()

    def get_user_exercises(self, user_id):
        with self.get_connection() as conn:
            query = "SELECT e.* FROM exercises e JOIN user_exercises ue ON e.id = ue.exercise_id WHERE ue.user_id = ?"
            return pd.read_sql(query, conn, params=(user_id,))

    def remove_user_exercise(self, user_id, exercise_id):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM user_exercises WHERE user_id = ? AND exercise_id = ?", (user_id, exercise_id))
            conn.commit()

    def promote_user(self, user_id):
        with self.get_connection() as conn:
            conn.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
            conn.commit()
        self._sync_to_csv('users')

    def delete_user(self, user_id):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
        self._sync_to_csv('users')

    def seed_exercises(self):
        with self.get_connection() as conn:
            if conn.execute("SELECT COUNT(*) FROM exercises").fetchone()[0] == 0:
                try:
                    df = pd.read_csv("data/exercises.csv")
                    df.to_sql("exercises", conn, if_exists="append", index=False)
                except: pass

    def update_user_details(self, user_id, username, age, height, weight, goal, frequency, is_admin):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = """
                UPDATE users 
                SET username = ?, age = ?, height = ?, weight = ?, goal = ?, frequency = ?, is_admin = ?
                WHERE id = ?
            """
            cursor.execute(query, (username, age, height, weight, goal, frequency, is_admin, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"DB Update Error: {e}")
            return False