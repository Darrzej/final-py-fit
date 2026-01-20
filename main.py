import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from dotenv import load_dotenv
import os

from utils.database import DatabaseManager
from utils.scraper import FitnessScraper

load_dotenv()
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Initialize OOP Objects
db = DatabaseManager()
scraper = FitnessScraper()

st.set_page_config("FitAI Pro", "💪", layout="wide")
db.seed_exercises()

if "user" not in st.session_state: st.session_state.user = None

# --- AUTH LOGIC ---
if st.session_state.user is None:
    st.title("🏋️ FitAI — Training System")
    t1, t2 = st.tabs(["Login", "Register"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            user_data = db.get_user(u, p)
            if user_data:
                st.session_state.user = user_data
                st.rerun()
            else: st.error("Invalid credentials.")
    with t2:
        ru = st.text_input("New Username")
        rp = st.text_input("New Password", type="password")
        c1, c2 = st.columns(2)
        age = c1.number_input("Age", 15, 100, 25)
        height = c2.number_input("Height (cm)", 100, 250, 175)
        weight = c1.number_input("Weight (kg)", 30, 300, 70)
        goal = c2.selectbox("Goal", ["bulk", "cut", "strength"])
        freq = c1.slider("Frequency", 1, 7, 3)
        if st.button("Create Account"):
            all_u = db.get_all_users()
            is_first = 1 if len(all_u) == 0 else 0
            if db.add_user(ru, rp, age, height, weight, goal, freq, is_admin=is_first):
                st.success("Account created!")
    st.stop()

# User Session variables
u_id, u_name, _, u_age, u_height, u_weight, u_goal, u_freq, u_admin = st.session_state.user

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"## 👤 {u_name}")
    st.metric("Body BMI", np.round(u_weight / ((u_height/100)**2), 1))
    st.divider()
    st.subheader("🍎 Nutrition Log")
    cal = st.number_input("Calories", 0, 10000, 2500)
    prot = st.number_input("Protein (g)", 0, 500, 140)
    if st.button("Save Daily Log"):
        db.add_nutrition_log(u_id, cal, prot, datetime.now().strftime("%Y-%m-%d"))
        st.toast("Saved & Mirrored to CSV")
    
    # WEB SCRAPING SECTION
    st.divider()
    st.subheader("🌐 Live Fitness News")
    with st.spinner("Fetching news..."):
        headlines = scraper.get_latest_articles()
        for h in headlines:
            st.caption(f"📍 {h}")
    
    st.divider()
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.rerun()

# --- MAIN TABS ---
tab_titles = ["📋 Program", "📈 Analytics", "🤖 AI Coach"]
if u_admin: tab_titles.append("🛠 Admin Panel")
tabs = st.tabs(tab_titles)

with tabs[0]: # PROGRAM
    st.header("Training Routine")
    my_ex = db.get_user_exercises(u_id)
    all_ex = db.get_exercises()
    my_ex_ids = set(my_ex["id"].tolist())
    with st.expander("🔍 Add Exercises"):
        search = st.text_input("Filter...")
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
        if c5.button("🗑️", key=f"d_{ex['id']}"):
            db.remove_user_exercise(u_id, ex["id"])
            st.rerun()

with tabs[1]: # ANALYTICS
    st.header("📊 Performance & Nutrition Analytics")
    with st.expander("❓ How to read the Nutrition chart"):
        st.write("Orange = Calories (Left Axis), Blue = Protein (Right Axis)")
    
    nutri_df = db.get_daily_nutrition_summary(u_id)
    if not nutri_df.empty:
        fig_nutri = make_subplots(specs=[[{"secondary_y": True}]])
        fig_nutri.add_trace(go.Scatter(x=nutri_df['date'], y=nutri_df['total_calories'], name="Calories", line=dict(color='#FFA500', width=3)), secondary_y=False)
        fig_nutri.add_trace(go.Scatter(x=nutri_df['date'], y=nutri_df['total_protein'], name="Protein", line=dict(color='#00BFFF', width=3)), secondary_y=True)
        fig_nutri.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig_nutri, use_container_width=True)
        with st.expander("📄 View Daily Intake Log (History)"):
            st.dataframe(nutri_df, use_container_width=True)
    
    st.divider()
    stats_df = db.get_user_stats(u_id)
    if not stats_df.empty:
        fig_pr = px.line(stats_df, x="updated_at", y="pr", color="name", markers=True, template="plotly_dark")
        st.plotly_chart(fig_pr, use_container_width=True)

with tabs[2]: # AI COACH
    st.header("🤖 FitAI Intelligence Report")
    
    if st.button("Generate Dynamic Analysis", type="primary"):
        with st.spinner("Processing biometric data..."):
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
                    report_items = res.json().get("report", [])
                    
                    st.subheader(f"Strategy for {u_name}")
                    
                    # Loop through the dynamic response and style accordingly
                    for item in report_items:
                        if item['type'] == "strength":
                            st.success(item['msg'])
                        elif item['type'] == "warning":
                            st.warning(item['msg'])
                        elif item['type'] == "plateau":
                            st.error(item['msg'])
                        elif item['type'] == "nutrition":
                            st.info(item['msg'])
                        else:
                            st.write(item['msg'])
                            
                    # Add a summary metric
                    if stats_df.empty or nutri_df.empty:
                        st.caption("Add more data to unlock the 'Consistency Score'.")
                    else:
                        st.balloons()
                else:
                    st.error("The API brain encountered a validation error.")
            except Exception as e:
                st.error(f"Could not reach AI Server: {e}")

if u_admin:
    with tabs[3]: # ADMIN
        st.header("👑 Admin Panel")
        all_users = db.get_all_users()
        st.dataframe(all_users, use_container_width=True)
        p_id = st.number_input("User ID to Promote", step=1)
        if st.button("Promote to Admin"):
            db.promote_user(p_id)
            st.rerun()