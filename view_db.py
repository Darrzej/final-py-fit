import sqlite3
import pandas as pd

conn = sqlite3.connect("data/fitai.db")

print("\n--- USERS ---")
print(pd.read_sql("SELECT * FROM users", conn))

print("\n--- EXERCISES ---")
print(pd.read_sql("SELECT * FROM exercises", conn))

print("\n--- USER EXERCISES ---")
print(pd.read_sql("SELECT * FROM user_exercises", conn))

print("\n--- USER STATS ---")
print(pd.read_sql("SELECT * FROM user_stats", conn))

conn.close()
