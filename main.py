import streamlit as st
import pandas as pd
import requests
from utils.database import create_tables, add_workout, get_all_workouts
from utils.analysis import compute_progress

st.set_page_config(page_title="FitAI Gym Tracker", page_icon="💪", layout="centered")

st.title("🏋️‍♂️ FitAI: Smart Gym Tracker & Virtual Coach")

# Ensure DB exists
create_tables()

# Workout logging form
st.header("📅 Log Your Workout")
with st.form("workout_form"):
    date = st.date_input("Date")
    exercise = st.text_input("Exercise name")
    sets = st.number_input("Sets", min_value=1, max_value=10, step=1)
    reps = st.number_input("Reps", min_value=1, max_value=50, step=1)
    weight = st.number_input("Weight (kg)", min_value=0.0, max_value=300.0, step=0.5)
    submit = st.form_submit_button("Add Workout")

    if submit:
        add_workout(str(date), exercise, sets, reps, weight)
        st.success("Workout added successfully! 💪")

# View workouts
st.header("📊 Your Progress")
df = get_all_workouts()
if df is not None and not df.empty:
    st.dataframe(df)

    # Show progress stats
    progress = compute_progress(df)
    if progress is not None:
        st.subheader("Average Volume per Exercise")
        st.bar_chart(progress)

    # Ask AI coach
    st.subheader("🤖 AI Coach Recommendation")
    try:
        payload = {"workouts": df.to_dict(orient="records")}
        response = requests.post("http://127.0.0.1:8000/recommend", json=payload)
        st.info(response.json()["recommendation"])
    except Exception as e:
        st.warning("Start the FastAPI server to get AI recommendations.")
else:
    st.info("No workouts logged yet. Add your first one above!")
