import streamlit as st
import pandas as pd
import requests
from utils.database import (
    create_tables, seed_exercises_from_csv, add_user, get_user,
    get_exercises, add_user_exercise, get_user_exercises,
    update_stat, get_user_stats, remove_user_exercise,
    get_all_users, delete_user, export_database
)

# Setup
st.set_page_config("FitAI", "💪", layout="wide")
create_tables()
seed_exercises_from_csv()

st.title("🏋️ FitAI — Smart Gym Tracker & AI Coach")

# --- AUTH ---
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.header("Login or Register")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            user = get_user(u, p)
            if user:
                st.session_state.user = user
                st.success("Logged in successfully")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        ru = st.text_input("New Username")
        rp = st.text_input("New Password", type="password")
        age = st.number_input("Age", 12, 100)
        height = st.number_input("Height (cm)", 100, 220)
        weight = st.number_input("Weight (kg)", 30, 200)
        goal = st.selectbox("Goal", ["bulk", "cut", "strength"])
        freq = st.slider("Training frequency (per week)", 1, 7, 3)

        if st.button("Register"):
            add_user(ru, rp, age, height, weight, goal, freq)
            st.success("Account created. You can login now.")

    st.stop()

# --- DASHBOARD ---
user = st.session_state.user
user_id = user[0]

tabs = st.tabs(["🏋️ Exercises", "📊 Stats", "🤖 AI Coach", "🛠 Admin"])


# --- EXERCISE SELECTION ---
with tabs[0]:
    st.header("Select Your Exercises")

    exercises = get_exercises()
    user_exercises = get_user_exercises(user_id)
    user_ex_ids = set(user_exercises["id"].tolist())

    for _, row in exercises.iterrows():
        if row["id"] in user_ex_ids:
            st.success(f"✔ {row['name']} already in your program")
        else:
            if st.button(f"Add {row['name']}", key=f"add_{row['id']}"):
                add_user_exercise(user_id, row["id"])
                st.rerun()

    st.subheader("Your Program")

    for _, ex in user_exercises.iterrows():
        col1, col2 = st.columns([3,1])
        col1.write(f"🏋️ {ex['name']} ({ex['muscle_group']})")
        if col2.button("❌ Remove", key=f"remove_{ex['id']}"):
            remove_user_exercise(user_id, ex["id"])
            st.rerun()


# --- STATS ---
with tabs[1]:
    st.header("Update Your PRs")

    user_exercises = get_user_exercises(user_id)

    for _, ex in user_exercises.iterrows():
        pr = st.number_input(
            f"{ex['name']} PR (kg)",
            0.0, 500.0,
            step=2.5,
            key=f"pr_{ex['id']}"
        )

        reps = st.number_input(
            f"{ex['name']} reps",
            1, 20,
            key=f"reps_{ex['id']}"
        )

        if st.button(f"Save {ex['name']}", key=f"save_{ex['id']}"):
            update_stat(user_id, ex["id"], pr, reps, pd.Timestamp.now().isoformat())
            st.success(f"{ex['name']} updated")

    st.subheader("Your Stats")
    st.dataframe(get_user_stats(user_id))

# --- AI COACH ---
with tabs[2]:
    st.header("🤖 Your AI Coach Report")

    stats_df = get_user_stats(user_id)

    payload = {
        "user": {
            "id": user[0],
            "username": user[1],
            "age": user[3],
            "height": user[4],
            "weight": user[5],
            "goal": user[6],
            "frequency": user[7]
        },
        "stats": stats_df.to_dict(orient="records")
    }

    try:
        res = requests.post("http://127.0.0.1:8000/coach", json=payload)
        for line in res.json()["report"]:
            st.info(line)
    except:
        st.warning("Start the FastAPI server to get AI coaching.")\
        
with tabs[3]:
    st.header("🛠 Admin Dashboard")

    # Make first user admin
    is_admin = user_id == 1

    if not is_admin:
        st.warning("Admin access only.")
        st.stop()

    st.subheader("All Users")
    users_df = get_all_users()
    st.dataframe(users_df)

    st.subheader("Delete User")
    delete_id = st.number_input("User ID to delete", min_value=1, step=1)

    if st.button("Delete User"):
        delete_user(delete_id)
        st.success("User deleted")
        st.rerun()

    st.subheader("Backup Database")

    if st.button("Export Database to CSV"):
        export_database()
        st.success("Database exported to CSV files")

