import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
from datetime import datetime
from dotenv import load_dotenv
import os

# Database and Scraper utilities
from utils.database import (
    create_tables, seed_exercises_from_csv, add_user, get_user,
    get_exercises, add_user_exercise, get_user_exercises,
    update_stat, get_user_stats, remove_user_exercise,
    get_all_users, export_database
)

# Configuration
load_dotenv()
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Setup Page
st.set_page_config("FitAI Dashboard", "💪", layout="wide")
create_tables()
seed_exercises_from_csv()

# --- AUTHENTICATION FLOW ---
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🏋️ FitAI — Smart Gym Tracker")
    st.subheader("Achieve your goals with data-driven coaching.")
    
    auth_tab1, auth_tab2 = st.tabs(["Login", "Register"])
    
    with auth_tab1:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("Login", use_container_width=True):
            user = get_user(u, p)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with auth_tab2:
        ru = st.text_input("Choose Username", key="reg_u")
        rp = st.text_input("Choose Password", type="password", key="reg_p")
        col1, col2 = st.columns(2)
        age = col1.number_input("Age", 15, 100, 25)
        height = col2.number_input("Height (cm)", 100, 250, 175)
        weight = col1.number_input("Weight (kg)", 30, 300, 70)
        goal = col2.selectbox("Fitness Goal", ["bulk", "cut", "strength"])
        freq = col1.slider("Training Days/Week", 1, 7, 3)
        
        if st.button("Create Account", use_container_width=True):
            if add_user(ru, rp, age, height, weight, goal, freq):
                st.success("Account created successfully! You can now login.")
            else:
                st.error("Username already exists.")
    st.stop()

# --- LOGGED IN STATE ---
user = st.session_state.user
user_id, username, _, age, height, weight, goal, frequency = user

# --- DYNAMIC & INTERACTIVE SIDEBAR ---
with st.sidebar:
    st.markdown(f"## 👤 {username}")
    st.markdown(f"**Goal:** {goal.capitalize()}")
    st.divider()
    
    # Advanced NumPy: BMI Calculation
    # Formula: kg / m^2
    bmi = np.round(weight / ((height / 100) ** 2), 1)
    
    st.metric("Body Mass Index (BMI)", bmi)
    
    # Progress Overview
    stats_df = get_user_stats(user_id)
    st.write(f"📊 **Total Logs:** {len(stats_df)}")
    
    st.divider()
    
    # Display Daily Tip via API Scraper Logic
    try:
        # Re-importing scraper logic for the sidebar
        from api.coach_api import get_dynamic_tip
        st.info(get_dynamic_tip())
    except:
        st.info("💡 Keep pushing! Consistency is the secret to growth.")

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        st.rerun()

# --- MAIN DASHBOARD TABS ---
st.title("Welcome Back!")
tabs = st.tabs(["📋 My Routine", "📊 Progress Analysis", "🤖 AI Coach", "🛠 Admin"])

# 1. PROGRAM TAB (CRUD: Add, Read, Log, Delete)
with tabs[0]:
    st.header("Training Routine")
    my_ex = get_user_exercises(user_id)
    all_ex = get_exercises()
    my_ex_ids = set(my_ex["id"].tolist())

    with st.expander("➕ Add Exercises to your Program"):
        search = st.text_input("Search exercises...")
        for _, ex in all_ex.iterrows():
            if ex["id"] not in my_ex_ids and (search.lower() in ex["name"].lower()):
                if st.button(f"Add {ex['name']} ({ex['muscle_group']})", key=f"add_{ex['id']}"):
                    add_user_exercise(user_id, ex["id"])
                    st.rerun()

    st.divider()
    st.subheader("Current Program")
    if my_ex.empty:
        st.info("Your routine is currently empty. Add exercises from the section above.")
    else:
        for _, ex in my_ex.iterrows():
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 1, 1])
            c1.markdown(f"### {ex['name']}")
            pr_val = c2.number_input("Weight (kg)", 0.0, 500.0, step=2.5, key=f"w_{ex['id']}")
            reps_val = c3.number_input("Reps", 1, 50, 8, key=f"r_{ex['id']}")
            
            if c4.button("Log PR", key=f"log_{ex['id']}"):
                update_stat(user_id, ex["id"], pr_val, reps_val, datetime.now().strftime("%Y-%m-%d %H:%M"))
                st.toast(f"Updated {ex['name']}!")

            # DELETE OPTION
            if c5.button("🗑️", key=f"del_{ex['id']}", help="Remove from routine"):
                remove_user_exercise(user_id, ex["id"])
                st.rerun()

# 2. PROGRESS TAB (Data Visualization)
with tabs[1]:
    st.header("Visual Strength Analysis")
    if not stats_df.empty:
        # Plotly Express Line Chart
        fig = px.line(
            stats_df, 
            x="updated_at", 
            y="pr", 
            color="name", 
            markers=True,
            title="Personal Record Trends",
            labels={"pr": "Weight (kg)", "updated_at": "Log Date"},
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No performance data found. Start logging workouts in the Program tab.")

# 3. AI COACH TAB (FastAPI Integration)
with tabs[2]:
    st.header("AI Coach Report")
    if st.button("Generate My Report"):
        payload = {
            "user": {
                "id": user_id, "username": username, "age": age, 
                "height": height, "weight": weight, "goal": goal, 
                "frequency": frequency
            },
            "stats": stats_df.to_dict(orient="records")
        }
        try:
            response = requests.post(f"{API_URL}/coach", json=payload)
            report = response.json()["report"]
            for message in report:
                st.info(message)
        except:
            st.error("Could not connect to the Coach API. Please ensure the FastAPI server is running.")

# 4. ADMIN TAB
with tabs[3]:
    if user_id == 1:
        st.subheader("Global User Database")
        st.dataframe(get_all_users(), use_container_width=True)
        if st.button("Download CSV Backup"):
            msg = export_database()
            st.success(msg)
    else:
        st.warning("Admin access required for this section.")