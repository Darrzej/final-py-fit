import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import os

# Import our custom OOP classes
from utils.database import DatabaseManager
from utils.scraper import FitnessScraper

# --- CONFIG & INITIALIZATION ---
st.set_page_config(page_title="FitAI Ultimate", page_icon="💪", layout="wide")

# Initialize OOP Objects
db = DatabaseManager()
scraper = FitnessScraper()
API_URL = "http://127.0.0.1:8000"

# Ensure exercises are seeded in the DB
db.seed_exercises()

# Session State for Authentication
if "user" not in st.session_state:
    st.session_state.user = None

# --- AUTHENTICATION UI ---
if st.session_state.user is None:
    st.title("🏋️ FitAI — Professional Training System")
    t1, t2 = st.tabs(["Login", "Register"])
    
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            user_data = db.get_user(u, p)
            if user_data:
                st.session_state.user = user_data
                st.rerun()
            else:
                st.error("Invalid credentials.")
                
    with t2:
        ru = st.text_input("New Username")
        rp = st.text_input("New Password", type="password")
        c1, c2 = st.columns(2)
        age = c1.number_input("Age", 15, 100, 25)
        height = c2.number_input("Height (cm)", 100, 250, 175)
        weight = c1.number_input("Weight (kg)", 30, 300, 70)
        goal = c2.selectbox("Goal", ["bulk", "cut", "strength"])
        freq = c1.slider("Training Frequency (days/week)", 1, 7, 3)
        if st.button("Create Account"):
            all_u = db.get_all_users()
            is_first = 1 if len(all_u) == 0 else 0
            if db.add_user(ru, rp, age, height, weight, goal, freq, is_admin=is_first):
                st.success("Account created successfully! Please login.")
    st.stop()

# --- USER DATA EXTRACTION ---
u_id, u_name, _, u_age, u_height, u_weight, u_goal, u_freq, u_admin = st.session_state.user

# --- SIDEBAR (Scraping & Quick Log) ---
with st.sidebar:
    st.markdown(f"## 👤 {u_name}")
    st.metric("Body BMI", np.round(u_weight / ((u_height/100)**2), 1))
    st.divider()
    
    st.subheader("🍎 Quick Nutrition Log")
    cal = st.number_input("Calories (kcal)", 0, 10000, 2500)
    prot = st.number_input("Protein (g)", 0, 500, 140)
    if st.button("Save Daily Log"):
        db.add_nutrition_log(u_id, cal, prot, datetime.now().strftime("%Y-%m-%d"))
        st.toast("Saved & Mirrored to CSV")
    
    st.divider()
    st.subheader("🌐 Live Fitness News (Scraped)")
    with st.spinner("Fetching latest news..."):
        headlines = scraper.get_latest_articles()
        for h in headlines:
            st.caption(f"📍 {h}")
    
    st.divider()
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.rerun()

# --- MAIN INTERFACE TABS ---
tab_titles = ["📋 Program", "📈 Analytics", "🤖 AI Coach", "🧮 Calculators"]
if u_admin:
    tab_titles.append("🛠 Admin Panel")
tabs = st.tabs(tab_titles)

# --- TAB 0: PROGRAM ---
with tabs[0]:
    st.header("Training Routine")
    my_ex = db.get_user_exercises(u_id)
    all_ex = db.get_exercises()
    my_ex_ids = set(my_ex["id"].tolist())
    
    with st.expander("🔍 Add Exercises to your Routine"):
        search = st.text_input("Search exercises...")
        for _, ex in all_ex.iterrows():
            if ex["id"] not in my_ex_ids and (search.lower() in ex["name"].lower()):
                if st.button(f"Add {ex['name']}", key=f"a_{ex['id']}"):
                    db.add_user_exercise(u_id, ex["id"])
                    st.rerun()
                    
    for _, ex in my_ex.iterrows():
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 1, 1])
        c1.write(f"### {ex['name']}")
        w = c2.number_input("kg", 0.0, 500.0, step=2.5, key=f"w_{ex['id']}")
        r = c3.number_input("reps", 1, 50, 8, key=f"r_{ex['id']}")
        if c4.button("Log", key=f"l_{ex['id']}"):
            db.update_stat(u_id, ex["id"], w, r, datetime.now().strftime("%Y-%m-%d %H:%M"))
            st.toast("PR Logged!")
        if c5.button("🗑️", key=f"d_{ex['id']}"):
            db.remove_user_exercise(u_id, ex["id"])
            st.rerun()

# --- TAB 1: ANALYTICS ---
with tabs[1]:
    st.header("📊 Performance & Nutrition Analytics")
    
    with st.expander("❓ How to read these charts"):
        st.write("""
        - **Nutrition Chart:** Tracks your fuel. Orange line is Calories, Blue line is Protein.
        - **Strength Chart:** Tracks your Power. Each line is a different exercise PR over time.
        - **History Table:** View the raw data you've logged daily.
        """)

    # 1. NUTRITION TRENDS
    st.subheader("🍎 Nutrition & Energy")
    nutri_df = db.get_daily_nutrition_summary(u_id)
    if not nutri_df.empty:
        fig_nutri = make_subplots(specs=[[{"secondary_y": True}]])
        fig_nutri.add_trace(go.Scatter(x=nutri_df['date'], y=nutri_df['total_calories'], name="Calories", 
                                      line=dict(color='#FFA500', width=3)), secondary_y=False)
        fig_nutri.add_trace(go.Scatter(x=nutri_df['date'], y=nutri_df['total_protein'], name="Protein", 
                                      line=dict(color='#00BFFF', width=3)), secondary_y=True)
        fig_nutri.update_layout(template="plotly_dark", height=400, hovermode="x unified")
        fig_nutri.update_yaxes(title_text="Calories (kcal)", secondary_y=False)
        fig_nutri.update_yaxes(title_text="Protein (g)", secondary_y=True)
        st.plotly_chart(fig_nutri, use_container_width=True)
        
        with st.expander("📄 View Daily Intake Log (History)"):
            st.dataframe(nutri_df.rename(columns={"date": "Date", "total_calories": "Calories", "total_protein": "Protein"}), use_container_width=True)
    else:
        st.info("No nutrition data yet.")

    st.divider()

    # 2. STRENGTH PROGRESS
    st.subheader("🏋️ Strength Progress (PRs)")
    stats_df = db.get_user_stats(u_id)
    if not stats_df.empty:
        fig_pr = px.line(stats_df, x="updated_at", y="pr", color="name", markers=True, template="plotly_dark",
                        labels={"pr": "Weight (kg)", "updated_at": "Date"})
        st.plotly_chart(fig_pr, use_container_width=True)
        
        with st.expander("🏆 All-Time Best Lifts"):
            best = stats_df.groupby('name')['pr'].max().reset_index()
            st.table(best)

# --- TAB 2: AI COACH (API Endpoint 1) ---
# ... (Imports and Auth remain the same as the previous full version)

with tabs[2]: # AI COACH (API Endpoint 1)
    st.header("🤖 FitAI Intelligence Report")
    st.write("Get a scientific and tactical breakdown of your training.")
    
    if st.button("Generate Performance Report", type="primary"):
        with st.spinner("Analyzing your database..."):
            stats_df = db.get_user_stats(u_id)
            nutri_df = db.get_daily_nutrition_summary(u_id)
            
            payload = {
                "username": u_name,
                "weight": u_weight,
                "goal": u_goal,
                "stats": stats_df.to_dict(orient="records"),
                "nutrition": nutri_df.to_dict(orient="records")
            }
            
            try:
                res = requests.post(f"{API_URL}/coach", json=payload)
                if res.status_code == 200:
                    report_data = res.json().get("report", [])
                    st.success(f"### Coach Analysis for {u_name}")
                    
                    for item in report_data:
                        if item['type'] == "strength":
                            st.info(item['msg'])
                        elif item['type'] == "success":
                            st.success(item['msg'])
                        elif item['type'] == "warning":
                            st.warning(item['msg'])
                        elif item['type'] == "plateau":
                            st.error(item['msg'])
                        else: # "info" type for general tips
                            st.write(item['msg'])
                            
                    st.balloons()
                else:
                    st.error("The API Brain is offline or returned an error.")
            except Exception as e:
                st.error(f"Connection Failed: {e}")

# ... (Calculators and Analytics remain intact)

# --- TAB 3: CALCULATORS (API Endpoint 2) ---
with tabs[3]:
    st.header("🧮 Strength Predictor (1RM)")
    c1, c2 = st.columns(2)
    calc_w = c1.number_input("Weight Lifted (kg)", 1.0, 500.0, 100.0)
    calc_r = c2.number_input("Reps", 1, 20, 5)
    
    if st.button("Predict Max Strength"):
        try:
            res = requests.post(f"{API_URL}/predict_1rm", json={"weight": calc_w, "reps": calc_r})
            if res.status_code == 200:
                data = res.json()
                st.metric("Estimated One-Rep Max", f"{data['one_rm']} kg")
                st.subheader("Training Zones")
                z_cols = st.columns(3)
                for i, (zone, val) in enumerate(data['zones'].items()):
                    z_cols[i].metric(zone, f"{val} kg")
        except: st.error("Calculator API Offline.")

# --- TAB 4: ADMIN ---
if u_admin:
    with tabs[4]:
        st.header("👑 Admin Panel")
        all_users = db.get_all_users()
        st.dataframe(all_users, use_container_width=True)
        uid_to_mod = st.number_input("Target User ID", step=1)
        if st.button("Promote to Admin"):
            db.promote_user(uid_to_mod)
            st.success(f"User {uid_to_mod} promoted.")