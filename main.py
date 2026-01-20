import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
from datetime import datetime
from dotenv import load_dotenv
import os

from utils.database import (
    create_tables, seed_exercises_from_csv, add_user, get_user,
    get_exercises, add_user_exercise, get_user_exercises,
    update_stat, get_user_stats, remove_user_exercise,
    get_all_users, export_database, add_nutrition_log, 
    get_user_nutrition, promote_user, delete_user
)

load_dotenv()
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config("FitAI Pro", "💪", layout="wide")
create_tables()
seed_exercises_from_csv()

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🏋️ FitAI — Advanced Training System")
    t1, t2 = st.tabs(["Login", "Register"])
    
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            user_data = get_user(u, p)
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
        freq = c1.slider("Frequency", 1, 7, 3)
        if st.button("Create Account", use_container_width=True):
            all_u = get_all_users()
            is_first = 1 if len(all_u) == 0 else 0
            if add_user(ru, rp, age, height, weight, goal, freq, is_admin=is_first):
                st.success("Account created! You can now login.")
    st.stop()

# --- APP DATA ---
user = st.session_state.user
u_id, u_name, _, u_age, u_height, u_weight, u_goal, u_freq, u_admin = user

with st.sidebar:
    st.markdown(f"## 👤 {u_name}")
    if u_admin:
        st.caption("🛡️ Administrator Access")
    
    bmi = np.round(u_weight / ((u_height/100)**2), 1)
    st.metric("Body BMI", bmi)
    
    st.divider()
    st.subheader("🍎 Nutrition Log")
    cal = st.number_input("Calories", 0, 10000, 2500)
    prot = st.number_input("Protein (g)", 0, 500, 140)
    if st.button("Save Daily Log", use_container_width=True):
        add_nutrition_log(u_id, cal, prot, datetime.now().strftime("%Y-%m-%d"))
        st.toast("Nutrition updated!")

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        st.rerun()

# Dynamic Tab Logic
tab_titles = ["📋 Program", "📈 Analytics", "🤖 AI Coach"]
if u_admin:
    tab_titles.append("🛠 Admin Panel")

tabs = st.tabs(tab_titles)

with tabs[0]:
    st.header("Training Routine")
    my_ex = get_user_exercises(u_id)
    all_ex = get_exercises()
    my_ex_ids = set(my_ex["id"].tolist())

    with st.expander("🔍 Add New Exercises"):
        search = st.text_input("Filter exercises...")
        for _, ex in all_ex.iterrows():
            if ex["id"] not in my_ex_ids and (search.lower() in ex["name"].lower()):
                if st.button(f"Add {ex['name']}", key=f"a_{ex['id']}"):
                    add_user_exercise(u_id, ex["id"])
                    st.rerun()

    for _, ex in my_ex.iterrows():
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 1, 1])
        c1.write(f"### {ex['name']}")
        w = c2.number_input("kg", 0.0, 500.0, step=2.5, key=f"w_{ex['id']}")
        r = c3.number_input("reps", 1, 50, 8, key=f"r_{ex['id']}")
        if c4.button("Log", key=f"l_{ex['id']}"):
            update_stat(u_id, ex["id"], w, r, datetime.now().strftime("%Y-%m-%d %H:%M"))
            st.toast("PR Saved!")
        if c5.button("🗑️", key=f"d_{ex['id']}"):
            remove_user_exercise(u_id, ex["id"])
            st.rerun()

with tabs[1]:
    stats_df = get_user_stats(u_id)
    if not stats_df.empty:
        fig = px.line(stats_df, x="updated_at", y="pr", color="name", markers=True, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Log some sessions to see your progress.")

with tabs[2]:
    if st.button("Generate AI Feedback"):
        nutri_df = get_user_nutrition(u_id)
        payload = {
            "user": {"id": u_id, "username": u_name, "age": u_age, "height": u_height, 
                     "weight": u_weight, "goal": u_goal, "frequency": u_freq},
            "stats": stats_df.to_dict(orient="records"),
            "nutrition": nutri_df.to_dict(orient="records")
        }
        try:
            res = requests.post(f"{API_URL}/coach", json=payload)
            for msg in res.json()["report"]:
                st.info(msg)
        except:
            st.error("API Offline.")

if u_admin:
    with tabs[3]:
        st.header("👑 Admin Panel")
        all_u = get_all_users()
        st.dataframe(all_u, use_container_width=True)
        
        c_p, c_d = st.columns(2)
        with c_p:
            p_id = st.number_input("Promote User ID", step=1, min_value=1)
            if st.button("Promote to Admin"):
                promote_user(p_id)
                st.success(f"User {p_id} promoted!")
                st.rerun()
        with c_d:
            d_id = st.number_input("Delete User ID", step=1, min_value=1)
            if st.button("Confirm User Deletion", type="primary"):
                delete_user(d_id)
                st.warning(f"User {d_id} removed.")
                st.rerun()
        
        if st.button("Export Database to CSV"):
            msg = export_database()
            st.success(msg)