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


def safe_request_json(method, url: str, friendly_name: str = "data", **kwargs):
    """
    Wrapper around requests.* that:
    - Catches connection errors and shows a clear message
    - Checks status_code before .json()
    - Catches JSON decode errors
    """
    try:
        resp = method(url, **kwargs)
    except requests.exceptions.ConnectionError:
        st.error("🔌 Unable to connect to the FitAI Server. Please check if the backend is running.")
        return None
    except Exception:
        st.error("⚠️ An unexpected error occurred while contacting the FitAI Server.")
        return None

    if resp.status_code != 200:
        st.warning(f"⚠️ Could not load {friendly_name} (server returned {resp.status_code}).")
        return None

    try:
        return resp.json()
    except ValueError:
        st.error("⚠️ Received invalid data from the FitAI Server.")
        return None

st.set_page_config(page_title="FitAI Ultimate", page_icon="💪", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None

# --- AUTHENTICATION ---
if st.session_state.user is None:
    st.title("🏋️ FitAI — Professional Training System")
    st.caption("Your intelligent fitness companion powered by AI")
    
    t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with t1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container(border=True):
                st.subheader("Welcome Back")
                u = st.text_input("👤 Username", placeholder="Enter your username")
                p = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
                if st.button("🚀 Login", type="primary", use_container_width=True):
                    try:
                        res = requests.post(f"{API_URL}/auth/login", json={"username": u, "password": p})
                    except requests.exceptions.ConnectionError:
                        st.error("🔌 Unable to connect to the FitAI Server. Please check if the backend is running.")
                    except Exception:
                        st.error("⚠️ An unexpected error occurred while contacting the FitAI Server.")
                    else:
                        if res.status_code == 200:
                            try:
                                st.session_state.user = res.json()
                                st.rerun()
                            except ValueError:
                                st.error("⚠️ Received invalid login data from the server.")
                        elif res.status_code == 401:
                            st.error("❌ Invalid credentials. Please try again.")
                        else:
                            st.warning(f"⚠️ Login failed (server returned {res.status_code}). Please try again later.")
    
    with t2:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container(border=True):
                st.subheader("Create Your Account")
                ru = st.text_input("👤 New Username", placeholder="Choose a username")
                rp = st.text_input("🔒 New Password", type="password", placeholder="Create a password")
                c1, c2 = st.columns(2)
                age = c1.number_input("🎂 Age", 15, 100, 25)
                height = c2.number_input("📏 Height (cm)", 100, 250, 175)
                weight = c1.number_input("⚖️ Weight (kg)", 30, 300, 70)
                goal = c2.selectbox("🎯 Goal", ["bulk", "cut", "strength"])
                freq = c1.slider("📅 Training Frequency (days/week)", 1, 7, 3)
        if st.button("✨ Create Account", type="primary", use_container_width=True):
            payload = {"username":ru, "password":rp, "age":age, "height":height, "weight":weight, "goal":goal, "frequency":freq}
            try:
                res = requests.post(f"{API_URL}/auth/register", json=payload)
            except requests.exceptions.ConnectionError:
                st.error("🔌 Unable to connect to the FitAI Server. Please check if the backend is running.")
            except Exception:
                st.error("⚠️ An unexpected error occurred while contacting the FitAI Server.")
            else:
                if res.status_code == 200:
                    st.success("✅ Account created successfully! Please login.")
                else:
                    st.warning(f"⚠️ Registration failed (server returned {res.status_code}). Please try again later.")
    st.stop()

user = st.session_state.user
u_id = user['id']

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"## 👤 {user['username']}")
    st.caption(f"Goal: {user['goal'].title()}")
    
    st.divider()
    
    with st.container(border=True):
        st.subheader("📊 Body Metrics")
        height_m = (user['height'] / 100) if user['height'] else 0
        if height_m > 0:
            bmi = np.round(user['weight'] / (height_m**2), 1)
            bmi_display = str(bmi)
        else:
            bmi_display = "N/A"
        st.metric("BMI", bmi_display)
        st.caption(f"Weight: {user['weight']} kg")
        st.caption(f"Height: {user['height']} cm")
    
    st.divider()
    
    with st.container(border=True):
        st.subheader("🍎 Quick Nutrition Log")
        cal = st.number_input("🔥 Calories", 0, 10000, 2500, help="Daily calorie intake")
        prot = st.number_input("🥩 Protein (g)", 0, 500, 140, help="Daily protein intake")
        if st.button("💾 Save Daily Log", type="primary", use_container_width=True):
            try:
                res = requests.post(
                    f"{API_URL}/log/nutrition",
                    json={
                        "user_id": u_id,
                        "calories": cal,
                        "protein": prot,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                    },
                )
            except requests.exceptions.ConnectionError:
                st.error("🔌 Unable to connect to the FitAI Server. Please check if the backend is running.")
            except Exception:
                st.error("⚠️ An unexpected error occurred while contacting the FitAI Server.")
            else:
                if res.status_code == 200:
                    st.toast("✅ Saved & Mirrored to CSV")
                else:
                    st.warning(f"⚠️ Failed to save nutrition log (server returned {res.status_code}).")
    
    st.divider()
    
    st.caption("📰 Latest Fitness News")
    with st.spinner("Fetching news..."):
        for h in scraper.get_latest_articles(): 
            st.caption(f"📍 {h}")
    
    st.divider()
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        st.rerun()

# --- TABS ---
titles = ["📋 Program", "📈 Analytics", "🤖 AI Coach", "🧮 Calculators"]
if user['is_admin']: titles.append("🛠 Admin Panel")
tabs = st.tabs(titles)

# TAB 0: PROGRAM
with tabs[0]:
    st.header("🏋️ Training Routine")
    st.caption("Log your workouts and track your progress")
    
    my_ex = safe_request_json(requests.get, f"{API_URL}/exercises/user/{u_id}", "user exercises") or []
    all_ex_list = safe_request_json(requests.get, f"{API_URL}/exercises/all", "exercise list") or []
    my_ex_ids = {e['id'] for e in my_ex}
    
    with st.expander("🔍 Add Exercises to Your Program"):
        with st.container(border=True):
            search = st.text_input("🔎 Search exercises...", placeholder="Type to filter exercises")
            
            # Get all exercises that can be added (not already in user's program)
            available_exercises = [ex for ex in all_ex_list if ex['id'] not in my_ex_ids]
            
            # Filter by search term if provided
            if search:
                available_exercises = [ex for ex in available_exercises if search.lower() in ex['name'].lower()]
            
            if available_exercises:
                st.caption(f"📋 Showing {len(available_exercises)} available exercise(s)")
                for ex in available_exercises:
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"**{ex['name']}**")
                    if col2.button("➕ Add", key=f"a_{ex['id']}", use_container_width=True):
                        try:
                            res = requests.post(
                                f"{API_URL}/exercises/add",
                                json={"user_id": u_id, "exercise_id": ex['id']},
                            )
                        except requests.exceptions.ConnectionError:
                            st.error("🔌 Unable to connect to the FitAI Server. Please check if the backend is running.")
                        except Exception:
                            st.error("⚠️ An unexpected error occurred while contacting the FitAI Server.")
                        else:
                            if res.status_code == 200:
                                st.toast(f"✅ Added {ex['name']}")
                                st.rerun()
                            else:
                                st.warning(f"⚠️ Failed to add exercise (server returned {res.status_code}).")
            else:
                if search:
                    st.info("🔍 No exercises found matching your search. Try a different term.")
                else:
                    st.info("✅ All available exercises have been added to your program!")
    
    st.divider()
    
    if my_ex:
        st.subheader("📋 Your Exercises")
        for ex in my_ex:
            with st.container(border=True):
                st.markdown(f"### 🏋️ {ex['name']}")
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                w = col1.number_input("⚖️ Weight (kg)", 0.0, 500.0, step=2.5, key=f"w_{ex['id']}", label_visibility="collapsed")
                col1.caption("Weight (kg)")
                r = col2.number_input("🔢 Reps", 1, 50, 8, key=f"r_{ex['id']}", label_visibility="collapsed")
                col2.caption("Reps")
                if col3.button("📝 Log Workout", key=f"l_{ex['id']}", type="primary", use_container_width=True):
                    try:
                        res = requests.post(
                            f"{API_URL}/log/workout",
                            json={
                                "user_id": u_id,
                                "exercise_id": ex['id'],
                                "weight": w,
                                "reps": r,
                                "date": datetime.now().strftime("%Y-%m-%d"),
                            },
                        )
                    except requests.exceptions.ConnectionError:
                        st.error("🔌 Unable to connect to the FitAI Server. Please check if the backend is running.")
                    except Exception:
                        st.error("⚠️ An unexpected error occurred while contacting the FitAI Server.")
                    else:
                        if res.status_code == 200:
                            st.toast("🎉 PR Logged!")
                        else:
                            st.warning(f"⚠️ Failed to log workout (server returned {res.status_code}).")
                if col4.button("🗑️", key=f"d_{ex['id']}", help="Remove exercise"):
                    try:
                        res = requests.post(
                            f"{API_URL}/exercises/remove",
                            json={"user_id": u_id, "exercise_id": ex['id']},
                        )
                    except requests.exceptions.ConnectionError:
                        st.error("🔌 Unable to connect to the FitAI Server. Please check if the backend is running.")
                    except Exception:
                        st.error("⚠️ An unexpected error occurred while contacting the FitAI Server.")
                    else:
                        if res.status_code == 200:
                            st.rerun()
                        else:
                            st.warning(f"⚠️ Failed to remove exercise (server returned {res.status_code}).")
    else:
        st.info("👆 Add exercises to your program using the search above to get started!")

# TAB 1: ANALYTICS (PRO VERSION)
with tabs[1]:
    st.markdown("### 📊 Performance & Metabolic Insights")
    st.caption("Track your fitness journey with detailed analytics")
    
    # 1. TOP LEVEL METRICS
    nutri_data = safe_request_json(requests.get, f"{API_URL}/data/nutrition/{u_id}", "nutrition data") or []
    stats_data = safe_request_json(requests.get, f"{API_URL}/data/stats/{u_id}", "stats data") or []
    
    with st.container(border=True):
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        
        if nutri_data:
            ndf = pd.DataFrame(nutri_data)
            avg_cal = int(ndf['total_calories'].mean())
            avg_prot = int(ndf['total_protein'].mean())
            m_col1.metric("🔥 Avg Daily Calories", f"{avg_cal} kcal", delta=None)
            m_col2.metric("🥩 Avg Daily Protein", f"{avg_prot} g", delta=None)
        else:
            m_col1.metric("🔥 Avg Daily Calories", "N/A", delta=None)
            m_col2.metric("🥩 Avg Daily Protein", "N/A", delta=None)
        
        m_col3.metric("⚖️ Current Weight", f"{user['weight']} kg")
        height_m = (user['height'] / 100) if user['height'] else 0
        if height_m > 0:
            bmi_val = np.round(user['weight'] / (height_m**2), 1)
            bmi_display = str(bmi_val)
        else:
            bmi_display = "N/A"
        m_col4.metric("📊 Body BMI", bmi_display)

    st.divider()

    # 2. METABOLIC TRENDS (Nutrition)
    with st.container(border=True):
        st.subheader("🍎 Metabolic Consistency")
        if nutri_data:
            ndf = pd.DataFrame(nutri_data)
            ndf['date'] = pd.to_datetime(ndf['date'])
            
            fig_nutri = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Calories - Area Chart for "Volume" feel
            fig_nutri.add_trace(go.Scatter(
                x=ndf['date'], y=ndf['total_calories'], 
                name="Calories", fill='tozeroy',
                line=dict(color='#00FFAA', width=3),
                marker=dict(size=8)
            ), secondary_y=False)
            
            # Protein - Line Chart
            fig_nutri.add_trace(go.Scatter(
                x=ndf['date'], y=ndf['total_protein'], 
                name="Protein",
                line=dict(color='#FF0077', width=4, dash='dot'),
            ), secondary_y=True)

            fig_nutri.update_layout(
                template="plotly_dark",
                hovermode="x unified",
                margin=dict(l=20, r=20, t=30, b=20),
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                yaxis=dict(showgrid=False, title="Energy (kcal)"),
                yaxis2=dict(showgrid=False, title="Recovery (g)"),
                xaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_nutri, use_container_width=True)
        else:
            st.info("📝 Log your meals to see metabolic trends.")

    st.divider()

    # 3. STRENGTH PROGRESSION
    with st.container(border=True):
        st.subheader("⚡ Strength Progression")
        if stats_data:
            sdf = pd.DataFrame(stats_data)
            sdf['updated_at'] = pd.to_datetime(sdf['updated_at'])
            
            # Cleaner Line Plot using Plotly Express
            fig_stats = px.line(
                sdf, x="updated_at", y="pr", color="name",
                markers=True, line_shape="spline", # Smooth lines
                template="plotly_dark",
                labels={"pr": "Weight (kg)", "updated_at": "Date", "name": "Exercise"}
            )
            
            fig_stats.update_layout(
                height=400,
                hovermode="closest",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            )
            fig_stats.update_traces(line=dict(width=4), marker=dict(size=10))
            
            st.plotly_chart(fig_stats, use_container_width=True)
        else:
            st.info("🏋️ Log your workouts to see strength analytics.")

# TAB 2: AI COACH (ENHANCED)
with tabs[2]:
    st.header("🤖 FitAI Intelligence Report")
    st.caption("Get personalized insights and recommendations from your AI coach")
    
    with st.container(border=True):
        if st.button("🚀 Generate Performance & Nutrition Report", type="primary", use_container_width=True):
            with st.spinner("🔍 Analyzing performance trends and metabolic logs..."):
                s_data = safe_request_json(requests.get, f"{API_URL}/data/stats/{u_id}", "stats data") or []
                n_data = safe_request_json(requests.get, f"{API_URL}/data/nutrition/{u_id}", "nutrition data") or []

                payload = {
                    "username": user['username'],
                    "weight": float(user['weight']),
                    "age": int(user['age']),
                    "goal": str(user['goal']),
                    "stats": s_data,
                    "nutrition": n_data,
                }

                res = safe_request_json(requests.post, f"{API_URL}/coach", "coach report", json=payload) or {}
            
            st.divider()
            
            if not res.get('report'):
                st.info("📊 I need more data to provide a tactical analysis. Log at least one workout and one meal.")
            else:
                # We group them for better UI flow
                st.subheader("📋 Tactical Feedback")
                for item in res['report']:
                    with st.container(border=True):
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
    st.caption("Calculate your one-rep max and training zones")
    
    with st.container(border=True):
        st.subheader("📊 Enter Your Lift Details")
        cw, cr = st.columns(2)
        w_val = cw.number_input("⚖️ Weight (kg)", 1.0, 500.0, 100.0, help="Weight lifted")
        r_val = cr.number_input("🔢 Reps", 1, 20, 5, help="Number of reps completed")
        
        if st.button("🎯 Predict Max", type="primary", use_container_width=True):
            res = safe_request_json(
                requests.post,
                f"{API_URL}/predict_1rm",
                "1RM prediction",
                json={"weight": w_val, "reps": r_val},
            ) or {}

            if "one_rm" in res:
                st.divider()

                with st.container(border=True):
                    st.success(f"💪 **Estimated 1RM: {res['one_rm']} kg**")
                    st.caption("Based on your lift of {:.1f} kg for {} reps".format(w_val, r_val))

                if "zones" in res:
                    st.divider()

                    st.subheader("📈 Training Zones")
                    z_cols = st.columns(3)
                    for i, (zone, val) in enumerate(res['zones'].items()):
                        with z_cols[i]:
                            with st.container(border=True):
                                st.metric(zone, f"{val} kg")

# TAB 4: ADMIN PANEL (WITH DELETE)
# Inside TAB 4: ADMIN PANEL
if user['is_admin']:
    with tabs[4]:
        st.header("👑 Global Database Management")
        st.caption("Administrative controls for managing the system")
        
        # TABLE SELECTOR
        with st.container(border=True):
            target_table = st.selectbox("📋 Select Table to Manage", 
                                        ["Users", "Exercises", "Workout Logs", "Nutrition Logs"],
                                        help="Choose which database table to view and manage")
        
        st.divider()

        
        if target_table == "Users":
            with st.container(border=True):
                st.subheader("👥 User Management")
                all_users = safe_request_json(requests.get, f"{API_URL}/admin/users", "user list") or []
                if all_users:
                    st.dataframe(pd.DataFrame(all_users), use_container_width=True, hide_index=True)
                else:
                    st.info("No users found in the database.")
            
            st.divider()
            
           
            with st.container(border=True):
                st.subheader("✏️ Edit User")
                edit_user_id = st.number_input("👤 User ID to Edit", step=1, min_value=1, key="edit_user_id")
                
                
                user_to_edit = next((u for u in all_users if u['id'] == edit_user_id), None)
                
                if user_to_edit:
                    with st.form("edit_user_form"):
                        col1, col2 = st.columns(2)
                        new_username = col1.text_input("👤 Username", value=user_to_edit.get('username', ''))
                        new_age = col1.number_input("🎂 Age", min_value=15, max_value=100, value=int(user_to_edit.get('age', 25)), step=1)
                        new_height = col2.number_input("📏 Height (cm)", min_value=100.0, max_value=250.0, value=float(user_to_edit.get('height', 175)), step=0.1)
                        new_weight = col2.number_input("⚖️ Weight (kg)", min_value=30.0, max_value=300.0, value=float(user_to_edit.get('weight', 70)), step=0.1)
                        new_goal = col1.selectbox("🎯 Goal", ["bulk", "cut", "strength"], 
                                                  index=["bulk", "cut", "strength"].index(user_to_edit.get('goal', 'bulk')) if user_to_edit.get('goal') in ["bulk", "cut", "strength"] else 0)
                        new_freq = col2.slider("📅 Training Frequency", min_value=1, max_value=7, value=int(user_to_edit.get('frequency', 3)), step=1)
                        new_is_admin = col1.checkbox("👑 Admin Status", value=bool(user_to_edit.get('is_admin', 0)))
                        
                        submitted = st.form_submit_button("💾 Update User", use_container_width=True)
                        
                    if submitted:
                        payload = {
                            "username": new_username,
                            "age": new_age,
                            "height": new_height,
                            "weight": new_weight,
                            "goal": new_goal,
                            "frequency": new_freq,
                            "is_admin": 1 if new_is_admin else 0
                        }
                        try:
                            response = requests.put(f"{API_URL}/admin/update_user/{edit_user_id}", json=payload)
                        except requests.exceptions.ConnectionError:
                            st.error("🔌 Unable to connect to the FitAI Server. Please check if the backend is running.")
                        except Exception:
                            st.error("⚠️ An unexpected error occurred while contacting the FitAI Server.")
                        else:
                            if response.status_code == 200:
                                st.success("✅ User updated successfully!")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to update user (server returned {response.status_code}).")
                else:
                    st.info("👆 Select a valid User ID from the table above to edit.")
            
            st.divider()
            
            # Delete User Section
            with st.container(border=True):
                st.subheader("🗑️ Delete User")
                delete_user_id = st.number_input("👤 User ID to Delete", step=1, min_value=1, key="delete_user_id")
                
                if st.button("⚠️ Permanently Delete User", type="primary", use_container_width=True):
                    try:
                        response = requests.delete(f"{API_URL}/admin/delete_user/{delete_user_id}")
                    except requests.exceptions.ConnectionError:
                        st.error("🔌 Unable to connect to the FitAI Server. Please check if the backend is running.")
                    except Exception:
                        st.error("⚠️ An unexpected error occurred while contacting the FitAI Server.")
                    else:
                        if response.status_code == 200:
                            st.success("✅ User deleted successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to delete user (server returned {response.status_code}).")

        # --- VIEW: EXERCISES ---
        elif target_table == "Exercises":
            with st.container(border=True):
                st.subheader("🏋️ Master Exercise Library")
                
                # Add New Exercise
                with st.expander("➕ Add New Exercise to Database"):
                    with st.container(border=True):
                        new_ex_name = st.text_input("📝 Exercise Name", placeholder="e.g., Barbell Squat")
                        new_ex_muscle = st.text_input("🎯 Target Muscle Group", "Full Body", placeholder="e.g., Legs, Chest, Back")
                        if st.button("💾 Save Exercise", type="primary", use_container_width=True):
                            try:
                                res = requests.post(
                                    f"{API_URL}/admin/exercises/add",
                                    json={"name": new_ex_name, "muscle_group": new_ex_muscle},
                                )
                            except requests.exceptions.ConnectionError:
                                st.error("🔌 Unable to connect to the FitAI Server. Please check if the backend is running.")
                            except Exception:
                                st.error("⚠️ An unexpected error occurred while contacting the FitAI Server.")
                            else:
                                if res.status_code == 200:
                                    st.success("✅ Added to library!")
                                    st.rerun()
                                else:
                                    st.warning(f"⚠️ Failed to add exercise (server returned {res.status_code}).")

            st.divider()

            # View/Delete Exercises
            with st.container(border=True):
                st.subheader("📊 Exercise Database")
                ex_list = safe_request_json(requests.get, f"{API_URL}/exercises/all", "exercise list") or []
                if ex_list:
                    df_ex = pd.DataFrame(ex_list)
                    st.dataframe(df_ex, use_container_width=True, hide_index=True)
                else:
                    st.info("No exercises found in the database.")
            
            st.divider()
            
            with st.container(border=True):
                st.subheader("🗑️ Delete Exercise")
                ex_del_id = st.number_input("Exercise ID to Delete", step=1, min_value=1)
                if st.button("⚠️ Permanently Delete Exercise", type="primary", use_container_width=True):
                    try:
                        res = requests.delete(f"{API_URL}/admin/table/exercises/{ex_del_id}")
                    except requests.exceptions.ConnectionError:
                        st.error("🔌 Unable to connect to the FitAI Server. Please check if the backend is running.")
                    except Exception:
                        st.error("⚠️ An unexpected error occurred while contacting the FitAI Server.")
                    else:
                        if res.status_code == 200:
                            st.success("✅ Exercise deleted!")
                            st.rerun()
                        else:
                            st.warning(f"⚠️ Failed to delete exercise (server returned {res.status_code}).")

        # --- VIEW: WORKOUT LOGS ---
        elif target_table == "Workout Logs":
            with st.container(border=True):
                st.subheader("📝 Edit Workout History")
                u_search = st.number_input("🔍 Filter by User ID", value=1, step=1, min_value=1)
                
                logs = safe_request_json(requests.get, f"{API_URL}/data/stats/{u_search}", "workout logs") or []
                
                if logs:
                    df_logs = pd.DataFrame(logs)
                    st.dataframe(df_logs, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    
                    with st.container(border=True):
                        st.subheader("✏️ Edit Log Entry")
                        log_id = st.number_input("Log Entry ID to Edit", step=1, min_value=1)
                        c1, c2 = st.columns(2)
                        new_w = c1.number_input("⚖️ New Weight (kg)", value=0.0, min_value=0.0)
                        new_r = c2.number_input("🔢 New Reps", value=0, step=1, min_value=0)
                        
                        if st.button("💾 Update Log Entry", type="primary", use_container_width=True):
                            try:
                                res = requests.put(
                                    f"{API_URL}/admin/logs/workout/{log_id}",
                                    json={"weight": new_w, "reps": new_r},
                                )
                            except requests.exceptions.ConnectionError:
                                st.error("🔌 Unable to connect to the FitAI Server. Please check if the backend is running.")
                            except Exception:
                                st.error("⚠️ An unexpected error occurred while contacting the FitAI Server.")
                            else:
                                if res.status_code == 200:
                                    st.success("✅ Log updated.")
                                    st.rerun()
                                else:
                                    st.warning(f"⚠️ Failed to update log (server returned {res.status_code}).")
                else:
                    st.info("📭 No logs found for this user.")

        # --- VIEW: NUTRITION LOGS ---
        elif target_table == "Nutrition Logs":
            with st.container(border=True):
                st.subheader("🍎 Global Nutrition Records")
                
                # Add a filter so the Admin can look up ANY user's nutrition
                u_search_nutri = st.number_input("🔍 Filter by User ID", value=u_id, step=1, min_value=1, key="nutri_search")
                
                try:
                    response = requests.get(f"{API_URL}/data/nutrition/{u_search_nutri}")
                except requests.exceptions.ConnectionError:
                    st.error("🔌 Unable to connect to the FitAI Server. Please check if the backend is running.")
                    response = None
                except Exception:
                    st.error("⚠️ An unexpected error occurred while contacting the FitAI Server.")
                    response = None

                if response and response.status_code == 200:
                    try:
                        data = response.json()
                    except ValueError:
                        st.error("⚠️ Received invalid nutrition data from the server.")
                        data = None
                    if data:
                        df = pd.DataFrame(data)
                        df.columns = ["Date", "Total Calories (kcal)", "Total Protein (g)"]
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        st.divider()
                        
                        col1, col2 = st.columns(2)
                        col1.metric("🔥 Avg Calories", f"{int(df['Total Calories (kcal)'].mean())} kcal")
                        col2.metric("🥩 Avg Protein", f"{int(df['Total Protein (g)'].mean())}g")
                    else:
                        st.info(f"📭 No nutrition logs found for User ID {u_search_nutri}")
                else:
                    st.error("❌ Could not fetch nutrition data.")

            st.divider()

            # --- ADDING THE INPUT FORM ---
            with st.container(border=True):
                st.subheader(f"➕ Manually Log Meal for User {u_search_nutri}")
                with st.form("nutrition_form_admin"):
                    cals = st.number_input("🔥 Calories", min_value=0, step=10, value=0)
                    prot = st.number_input("🥩 Protein (g)", min_value=0, step=1, value=0)
                    date = st.date_input("📅 Date")
                    
                    if st.form_submit_button("💾 Save Log", use_container_width=True):
                        log_data = {
                            "user_id": u_search_nutri, # Uses the ID from the search box
                            "calories": cals,
                            "protein": prot,
                            "date": str(date)
                        }
                        try:
                            res = requests.post(f"{API_URL}/log/nutrition", json=log_data)
                        except requests.exceptions.ConnectionError:
                            st.error("🔌 Unable to connect to the FitAI Server. Please check if the backend is running.")
                        except Exception:
                            st.error("⚠️ An unexpected error occurred while contacting the FitAI Server.")
                        else:
                            if res.status_code == 200:
                                st.success("✅ Log saved!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to save log.")