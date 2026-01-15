import sqlite3
import pandas as pd

conn = sqlite3.connect("data/fitai.db")

username = input("Enter username: ")

query = """
SELECT e.name, us.pr, us.reps, us.updated_at
FROM users u
JOIN user_stats us ON u.id = us.user_id
JOIN exercises e ON e.id = us.exercise_id
WHERE u.username = ?
"""

df = pd.read_sql(query, conn, params=(username,))
print(df)

conn.close()
