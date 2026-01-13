import streamlit as st
import pandas as pd
import requests
from utils.database import (
    create_tables, seed_exercises_from_csv, add_user, get_user,
    get_exercises, add_user_exercise, get_user_exercises,
    update_stat, get_user_stats
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

tabs = st.tabs(["🏋️ Exercises", "📊 Stats", "🤖 AI Coach"])

# --- EXERCISE SELECTION ---
with tabs[0]:
    st.header("Select Your Exercises")
    exercises = get_exercises()
    for _, row in exercises.iterrows():
        if st.button(f"Add {row['name']}"):
            add_user_exercise(user_id, row["id"])
            st.success(f"{row['name']} added to your program")

    st.subheader("Your Program")
    st.dataframe(get_user_exercises(user_id))

# --- STATS ---
with tabs[1]:
    st.header("Update Your PRs")
    user_exercises = get_user_exercises(user_id)

    for _, ex in user_exercises.iterrows():
        pr = st.number_input(f"{ex['name']} PR (kg)", 0.0, 500.0, step=2.5)
        reps = st.number_input(f"{ex['name']} reps", 1, 20)
        if st.button(f"Save {ex['name']}"):
            update_stat(user_id, ex["id"], pr, reps, pd.Timestamp.now().isoformat())
            st.success("Saved")

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
        st.warning("Start the FastAPI server to get AI coaching.")
