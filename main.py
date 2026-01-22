import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from utils.scraper import FitnessScraper

API_URL = "http://127.0.0.1:8000"
scraper = FitnessScraper()

st.set_page_config(page_title="FitAI Ultimate", page_icon="💪", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None

# --- AUTHENTICATION ---
if st.session_state.user is None:
    st.title("🏋️ FitAI — Professional Training System")
    t1, t2 = st.tabs(["Login", "Register"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            res = requests.post(f"{API_URL}/auth/login", json={"username": u, "password": p})
            if res.status_code == 200:
                st.session_state.user = res.json()
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
            payload = {"username":ru, "password":rp, "age":age, "height":height, "weight":weight, "goal":goal, "frequency":freq}
            requests.post(f"{API_URL}/auth/register", json=payload)
            st.success("Account created successfully!")
    st.stop()

user = st.session_state.user
u_id = user['id']

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"## 👤 {user['username']}")
    st.metric("Body BMI", np.round(user['weight'] / ((user['height']/100)**2), 1))
    st.divider()
    st.subheader("🍎 Quick Nutrition Log")
    cal = st.number_input("Calories", 0, 10000, 2500)
    prot = st.number_input("Protein", 0, 500, 140)
    if st.button("Save Daily Log"):
        requests.post(f"{API_URL}/log/nutrition", json={"user_id": u_id, "calories": cal, "protein": prot, "date": datetime.now().strftime("%Y-%m-%d")})
        st.toast("Saved & Mirrored to CSV")
    st.divider()
    with st.spinner("Fetching news..."):
        for h in scraper.get_latest_articles(): st.caption(f"📍 {h}")
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.rerun()

# --- TABS ---
titles = ["📋 Program", "📈 Analytics", "🤖 AI Coach", "🧮 Calculators"]
if user['is_admin']: titles.append("🛠 Admin Panel")
tabs = st.tabs(titles)

# TAB 0: PROGRAM
with tabs[0]:
    st.header("Training Routine")
    my_ex = requests.get(f"{API_URL}/exercises/user/{u_id}").json()
    all_ex_list = requests.get(f"{API_URL}/exercises/all").json()
    my_ex_ids = {e['id'] for e in my_ex}
    
    with st.expander("🔍 Add Exercises"):
        search = st.text_input("Search...")
        for ex in all_ex_list:
            if ex['id'] not in my_ex_ids and search.lower() in ex['name'].lower():
                if st.button(f"Add {ex['name']}", key=f"a_{ex['id']}"):
                    requests.post(f"{API_URL}/exercises/add", json={"user_id": u_id, "exercise_id": ex['id']})
                    st.rerun()
    
    for ex in my_ex:
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 1, 1])
        c1.write(f"### {ex['name']}")
        w = c2.number_input("kg", 0.0, 500.0, step=2.5, key=f"w_{ex['id']}")
        r = c3.number_input("reps", 1, 50, 8, key=f"r_{ex['id']}")
        if c4.button("Log", key=f"l_{ex['id']}"):
            requests.post(f"{API_URL}/log/workout", json={"user_id": u_id, "exercise_id": ex['id'], "weight": w, "reps": r, "date": datetime.now().strftime("%Y-%m-%d")})
            st.toast("PR Logged!")
        if c5.button("🗑️", key=f"d_{ex['id']}"):
            requests.post(f"{API_URL}/exercises/remove", json={"user_id": u_id, "exercise_id": ex['id']})
            st.rerun()

# TAB 1: ANALYTICS
with tabs[1]:
    st.header("📊 Performance Analytics")
    nutri_data = requests.get(f"{API_URL}/data/nutrition/{u_id}").json()
    if nutri_data:
        ndf = pd.DataFrame(nutri_data)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=ndf['date'], y=ndf['total_calories'], name="Calories", line=dict(color='#FFA500', width=3)), secondary_y=False)
        fig.add_trace(go.Scatter(x=ndf['date'], y=ndf['total_protein'], name="Protein", line=dict(color='#00BFFF', width=3)), secondary_y=True)
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)

    stats_data = requests.get(f"{API_URL}/data/stats/{u_id}").json()
    if stats_data:
        sdf = pd.DataFrame(stats_data)
        st.plotly_chart(px.line(sdf, x="updated_at", y="pr", color="name", markers=True, template="plotly_dark"), use_container_width=True)

# TAB 2: AI COACH (ENHANCED)
with tabs[2]:
    st.header("🤖 FitAI Intelligence Report")
    
    if st.button("Generate Performance & Nutrition Report", type="primary"):
        with st.spinner("Analyzing performance trends and metabolic logs..."):
            s_data = requests.get(f"{API_URL}/data/stats/{u_id}").json()
            n_data = requests.get(f"{API_URL}/data/nutrition/{u_id}").json()
            
            payload = {
                "username": user['username'], 
                "weight": float(user['weight']), 
                "age": int(user['age']),         
                "goal": str(user['goal']), 
                "stats": s_data, 
                "nutrition": n_data
            }
            
            res = requests.post(f"{API_URL}/coach", json=payload).json()
        
        st.divider()
        
        if not res.get('report'):
            st.info("I need more data to provide a tactical analysis. Log at least one workout and one meal.")
        else:
            # We group them for better UI flow
            st.subheader("📋 Tactical Feedback")
            for item in res['report']:
                if item['type'] == "strength":
                    st.info(item['msg'], icon="💪")
                elif item['type'] == "warning":
                    st.warning(item['msg'], icon="⚠️")
                elif item['type'] == "plateau":
                    st.error(item['msg'], icon="🛑")
                elif item['type'] == "success":
                    st.success(item['msg'], icon="✅")
                else:
                    st.chat_message("assistant").write(item['msg'])
            
            st.balloons() 
# TAB 3: CALCULATORS
with tabs[3]:
    st.header("🧮 1RM Predictor")
    cw, cr = st.columns(2)
    w_val = cw.number_input("Weight (kg)", 1.0, 500.0, 100.0)
    r_val = cr.number_input("Reps", 1, 20, 5)
    if st.button("Predict Max"):
        res = requests.post(f"{API_URL}/predict_1rm", json={"weight": w_val, "reps": r_val}).json()
        st.metric("Estimated 1RM", f"{res['one_rm']} kg")
        z_cols = st.columns(3)
        for i, (zone, val) in enumerate(res['zones'].items()):
            z_cols[i].metric(zone, f"{val} kg")

# TAB 4: ADMIN PANEL (WITH DELETE)
if user['is_admin']:
    with tabs[4]:
        st.header("👑 Admin Panel")
        all_users = requests.get(f"{API_URL}/admin/users").json()
        st.dataframe(pd.DataFrame(all_users), use_container_width=True)
        
        st.divider()
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Promote")
            target_p = st.number_input("User ID to Promote", step=1, key="p_id")
            if st.button("Promote to Admin"):
                requests.post(f"{API_URL}/admin/promote/{target_p}")
                st.success("User promoted.")
                st.rerun()
                
        with c2:
            st.subheader("Delete")
            target_d = st.number_input("User ID to Delete", step=1, key="d_id")
            confirm = st.checkbox(f"Confirm Delete ID {target_d}")
            if st.button("Delete User", type="primary"):
                if confirm:
                    requests.delete(f"{API_URL}/admin/delete_user/{target_d}")
                    st.warning("User deleted.")
                    st.rerun()
                else:
                    st.error("Check confirmation box!")