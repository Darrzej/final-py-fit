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
    get_all_users, add_nutrition_log, 
    get_user_nutrition, promote_user, delete_user, get_daily_nutrition_summary
)

load_dotenv()
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config("FitAI Pro", "💪", layout="wide")
create_tables()
seed_exercises_from_csv()

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🏋️ FitAI — Training System")
    t1, t2 = st.tabs(["Login", "Register"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
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
        if st.button("Create Account"):
            all_u = get_all_users()
            is_first = 1 if len(all_u) == 0 else 0
            if add_user(ru, rp, age, height, weight, goal, freq, is_admin=is_first):
                st.success("Account created!")
    st.stop()

user = st.session_state.user
u_id, u_name, _, u_age, u_height, u_weight, u_goal, u_freq, u_admin = user

with st.sidebar:
    st.markdown(f"## 👤 {u_name}")
    bmi = np.round(u_weight / ((u_height/100)**2), 1)
    st.metric("Body BMI", bmi)
    st.divider()
    st.subheader("🍎 Nutrition Log")
    cal = st.number_input("Calories", 0, 10000, 2500)
    prot = st.number_input("Protein (g)", 0, 500, 140)
    if st.button("Save Daily Log"):
        add_nutrition_log(u_id, cal, prot, datetime.now().strftime("%Y-%m-%d"))
        st.toast("Syncing CSV...")

    st.divider()
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.rerun()

tab_titles = ["📋 Program", "📈 Analytics", "🤖 AI Coach"]
if u_admin:
    tab_titles.append("🛠 Admin Panel")

tabs = st.tabs(tab_titles)

with tabs[0]:
    st.header("Training Routine")
    my_ex = get_user_exercises(u_id)
    all_ex = get_exercises()
    my_ex_ids = set(my_ex["id"].tolist())
    with st.expander("🔍 Add Exercises"):
        search = st.text_input("Filter...")
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
        if c5.button("🗑️", key=f"d_{ex['id']}"):
            remove_user_exercise(u_id, ex["id"])
            st.rerun()

with tabs[1]: # ANALYTICS
    st.header("📊 Performance & Nutrition Analytics")

    # --- SECTION 1: NUTRITION TRENDS ---
    st.subheader("🍎 Nutrition & Energy")
    
    # 1. GUIDE (Help section)
    with st.expander("❓ How to read the Nutrition chart"):
        st.write("""
        This chart tracks your daily nutritional consistency.
        - **Orange Line (Left):** Your daily calorie intake (kcal).
        - **Blue Line (Right):** Your daily protein intake (grams).
        - Consistency is key! Aim to keep these lines as steady as possible.
        """)

    nutri_df = get_daily_nutrition_summary(u_id)
    
    if not nutri_df.empty:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        # 2. THE CHART
        fig_nutri = make_subplots(specs=[[{"secondary_y": True}]])

        # Track Calories (Orange Line)
        fig_nutri.add_trace(
            go.Scatter(
                x=nutri_df['date'], 
                y=nutri_df['total_calories'], 
                name="Calories", 
                mode='lines+markers',
                line=dict(color='#FFA500', width=3),
                hovertemplate="%{y} kcal"
            ),
            secondary_y=False,
        )

        # Track Protein (Blue Line)
        fig_nutri.add_trace(
            go.Scatter(
                x=nutri_df['date'], 
                y=nutri_df['total_protein'], 
                name="Protein", 
                mode='lines+markers',
                line=dict(color='#00BFFF', width=3),
                hovertemplate="%{y}g Protein"
            ),
            secondary_y=True,
        )

        fig_nutri.update_layout(
            template="plotly_dark",
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
            margin=dict(l=20, r=20, t=30, b=20),
            height=400
        )

        fig_nutri.update_yaxes(title_text="<b>Calories (kcal)</b>", color="#FFA500", secondary_y=False)
        fig_nutri.update_yaxes(title_text="<b>Protein (g)</b>", color="#00BFFF", secondary_y=True)

        st.plotly_chart(fig_nutri, use_container_width=True)

        # 3. HISTORY TABLE (Daily Intake Log)
        with st.expander("📄 View Daily Intake Log (History)"):
            display_df = nutri_df.rename(columns={
                "date": "Date", 
                "total_calories": "Calories (kcal)", 
                "total_protein": "Protein (g)"
            })
            st.dataframe(display_df, use_container_width=True)
            
    else:
        st.info("No nutrition data logged yet. Use the sidebar to track your meals.")

    st.divider()

    # --- SECTION 2: STRENGTH PROGRESS (PRs) ---
    st.subheader("🏋️ Strength Progress (PRs)")
    stats_df = get_user_stats(u_id)
    
    if not stats_df.empty:
        # 4. THE STRENGTH CHART
        fig_pr = px.line(
            stats_df, 
            x="updated_at", 
            y="pr", 
            color="name", 
            markers=True,
            title="Personal Records by Exercise",
            labels={"pr": "Weight (kg)", "updated_at": "Date", "name": "Exercise"},
            template="plotly_dark"
        )
        
        fig_pr.update_traces(line=dict(width=3))
        fig_pr.update_layout(
            hovermode="closest",
            margin=dict(l=20, r=20, t=50, b=20),
            height=450
        )
        
        st.plotly_chart(fig_pr, use_container_width=True)
        
        # 5. BEST LIFTS TABLE
        with st.expander("🏆 View Your All-Time Best Lifts"):
            best_lifts = stats_df.groupby('name')['pr'].max().sort_values(ascending=False).reset_index()
            best_lifts.columns = ["Exercise", "Max Weight (kg)"]
            st.table(best_lifts)
            
    else:
        st.info("No lift data found. Log your workouts in the 'Program' tab to see your progress!")

with tabs[2]:
    if st.button("Run AI Analysis"):
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
        st.caption("ℹ️ All changes below are automatically mirrored to the CSV backup folder.")
        
        c_p, c_d = st.columns(2)
        with c_p:
            p_id = st.number_input("Promote User ID", step=1, min_value=1)
            if st.button("Promote to Admin"):
                promote_user(p_id)
                st.rerun()
        with c_d:
            d_id = st.number_input("Delete User ID", step=1, min_value=1)
            if st.button("Confirm User Deletion", type="primary"):
                delete_user(d_id)
                st.rerun()