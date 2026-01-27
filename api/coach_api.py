from fastapi import FastAPI, HTTPException
from api.models.user import UserCreate, UserLogin, UserUpdate
from api.models.exercise import WorkoutLog, ExerciseAction, ExerciseCreate, WorkoutUpdate
from api.models.nutrition import NutritionLog, NutritionUpdate
from api.models.coach import CoachRequest, OneRMRequest, LogUpdate
from utils.database import DatabaseManager
import pandas as pd

app = FastAPI()
db = DatabaseManager()

# --- AUTHENTICATION ---
@app.post("/auth/login")
def login(data: UserLogin):
    try:
        user = db.get_user(data.username, data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {
            "id": user[0], "username": user[1], "age": user[3],
            "height": user[4], "weight": user[5], "goal": user[6],
            "frequency": user[7], "is_admin": user[8]
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to process login request.")

@app.post("/auth/register")
def register(u: UserCreate):
    try:
        return db.add_user(u.username, u.password, u.age, u.height, u.weight, u.goal, u.frequency, u.is_admin)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to register user.")

# --- DATA RETRIEVAL ---
@app.get("/data/stats/{user_id}")
def get_stats(user_id: int):
    try:
        df = db.get_user_stats(user_id)
        return df.to_dict(orient="records")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch stats data.")

@app.get("/data/nutrition/{user_id}")
def get_nutri(user_id: int):
    try:
        df = db.get_daily_nutrition_summary(user_id)
        return df.to_dict(orient="records")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch nutrition data.")

@app.get("/exercises/all")
def all_ex():
    try:
        return db.get_exercises().to_dict(orient="records")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch exercise list.")

@app.get("/exercises/user/{user_id}")
def user_ex(user_id: int):
    try:
        return db.get_user_exercises(user_id).to_dict(orient="records")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch user exercises.")

# --- LOGGING & ACTIONS ---
@app.post("/log/workout")
def log_work(d: WorkoutLog):
    try:
        return db.update_stat(d.user_id, d.exercise_id, d.weight, d.reps, d.date)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to log workout.")

@app.post("/log/nutrition")
def log_nutri(d: NutritionLog):
    try:
        return db.add_nutrition_log(d.user_id, d.calories, d.protein, d.date)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to log nutrition.")

@app.post("/exercises/add")
def add_ex(d: ExerciseAction):
    try:
        return db.add_user_exercise(d.user_id, d.exercise_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add exercise to user program.")

@app.post("/exercises/remove")
def rem_ex(d: ExerciseAction):
    try:
        return db.remove_user_exercise(d.user_id, d.exercise_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to remove exercise from user program.")

# --- DYNAMIC AI COACH ---
@app.post("/coach")
def get_advice(data: CoachRequest):
    try:
        advice = []
        stats_df = pd.DataFrame(data.stats) if data.stats else pd.DataFrame()
        nutri_df = pd.DataFrame(data.nutrition) if data.nutrition else pd.DataFrame()
        goal = data.goal.lower()
        weight = data.weight
        age = data.age

        # If there is no stats or nutrition data, return a friendly message
        if stats_df.empty and nutri_df.empty:
            return {
                "report": [
                    {
                        "type": "info",
                        "msg": "Not enough data yet. Log at least one workout and one meal to receive an in-depth AI analysis."
                    }
                ]
            }

        if weight is None or weight <= 0:
            raise HTTPException(status_code=400, detail="Invalid weight value for analysis.")

        # --- 1. BIOMETRIC & AGE ANALYSIS ---
        if age < 25:
            advice.append({"type": "info", "msg": "🧬 **Metabolic Profile:** At your age, your recovery capacity is peak. You can handle higher training volume (reps/sets) than older athletes."})
        elif age > 45:
            advice.append({"type": "warning", "msg": "🧬 **Recovery Profile:** Joint integrity and hormonal recovery take longer at 45+. Prioritize 8 hours of sleep and consider a 1:4 deload cycle (3 weeks on, 1 week light)."})

        # --- 2. GLOBAL STRENGTH ASSESSMENT ---
        if not stats_df.empty:
            # Strength Standards (Multiplier of Bodyweight)
            standards = {
                "Bench Press": {"beg": 0.7, "int": 1.0, "adv": 1.5},
                "Squat": {"beg": 1.0, "int": 1.5, "adv": 2.0},
                "Deadlift": {"beg": 1.25, "int": 1.8, "adv": 2.5},
                "Overhead Press": {"beg": 0.5, "int": 0.75, "adv": 1.0}
            }

            # Get latest PR for every unique exercise
            latest_lifts = stats_df.sort_values('updated_at').groupby('name').last()

            for name, row in latest_lifts.iterrows():
                pr = row['pr']
                ratio = pr / weight

                # Check against standards if it's a major lift
                if name in standards:
                    std = standards[name]
                    if ratio < std['beg']:
                        level = "Novice"
                        status = "info"
                    elif ratio < std['int']:
                        level = "Intermediate"
                        status = "success"
                    else:
                        level = "Advanced/Elite"
                        status = "strength"

                    advice.append({"type": status, "msg": f"🏋️ **{name} Check:** Your {pr}kg lift is {round(ratio,2)}x BW ({level}). Focus on form and consistent loading."})
                else:
                    # For non-major lifts, just check the trend
                    advice.append({"type": "info", "msg": f"💪 **{name}:** You are currently moving {pr}kg. Keep tracking to see your 4-week trend."})

            # --- 3. PROGRESSION CHECK (DELTAS) ---
            for name in stats_df['name'].unique():
                ex_history = stats_df[stats_df['name'] == name]
                if len(ex_history) >= 2:
                    recent = ex_history.iloc[-1]['pr']
                    prev = ex_history.iloc[-2]['pr']
                    if recent > prev:
                        advice.append({"type": "success", "msg": f"🔥 **PR Alert:** You increased your {name} by {round(recent-prev,1)}kg. This is effective 'Overload'!"})

        # --- 4. NUTRITION & CALORIC JUDGMENT ---
        if not nutri_df.empty:
            avg_cal = nutri_df.tail(5)['total_calories'].mean()
            avg_prot = nutri_df.tail(5)['total_protein'].mean()
            prot_ratio = avg_prot / weight

            # Caloric check based on goal
            if goal == "bulk" and avg_cal < (weight * 34):
                advice.append({"type": "warning", "msg": f"🍎 **Bulk Warning:** You're averaging {int(avg_cal)} kcal. For growth at {weight}kg, you need closer to {int(weight * 38)} kcal."})
            elif goal == "cut" and avg_cal > (weight * 28):
                advice.append({"type": "warning", "msg": f"📉 **Cut Warning:** Your calories ({int(avg_cal)}) are a bit high for fat loss. Aim for ~{int(weight * 24)} kcal."})

            # Protein Floor
            if prot_ratio < 1.6:
                advice.append({"type": "plateau", "msg": f"🥩 **Protein Deficiency:** {round(prot_ratio,1)}g/kg is too low. To protect muscle, aim for {int(weight * 2.0)}g total protein."})
            else:
                advice.append({"type": "success", "msg": f"✅ **Protein Target Hit:** {round(prot_ratio,1)}g/kg is excellent for recovery."})

        return {"report": advice}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate coaching advice.")

@app.post("/predict_1rm")
def predict(d: OneRMRequest):
    try:
        if d.reps <= 0 or d.reps >= 37:
            raise HTTPException(status_code=400, detail="Reps must be between 1 and 36 for 1RM prediction.")
        one_rm = d.weight * (36 / (37 - d.reps)) if d.reps > 1 else d.weight
        return {"one_rm": round(one_rm, 1)}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to calculate 1RM prediction.")

# --- ADMIN PANEL ROUTES ---
@app.get("/admin/users")
def get_users():
    try:
        return db.get_all_users().to_dict(orient="records")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch users.")

@app.post("/admin/promote/{user_id}")
def promote(user_id: int):
    try:
        return db.promote_user(user_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to promote user.")

@app.delete("/admin/delete_user/{user_id}")
def delete_user(user_id: int):
    try:
        db.delete_user(user_id)
        return {"status": "deleted"}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete user.")

@app.put("/admin/update_user/{user_id}")
def update_user_details(user_id: int, data: UserUpdate):
    try:
        success = db.update_user_details(
            user_id, data.username, data.age, data.height,
            data.weight, data.goal, data.frequency, data.is_admin
        )
        if not success:
            raise HTTPException(status_code=400, detail="Update failed")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update user details.")

@app.post("/admin/exercises/add")
def admin_add_ex(ex: ExerciseCreate):
    try:
        db.add_master_exercise(ex.name, ex.muscle_group)
        return {"status": "added"}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add exercise.")

@app.delete("/admin/table/{table_name}/{row_id}")
def admin_delete(table_name: str, row_id: int):
    try:
        db.delete_from_table(table_name, row_id)
        return {"status": "deleted"}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete record.")

@app.put("/admin/logs/workout/{row_id}")
def update_w_log(row_id: int, d: WorkoutUpdate):
    try:
        db.update_log("user_stats", row_id, d.weight, d.reps)
        return {"status": "updated"}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update workout log.")

@app.put("/admin/logs/nutrition/{row_id}")
def update_n_log(row_id: int, d: NutritionUpdate):
    try:
        db.update_log("user_nutrition", row_id, d.calories, d.protein)
        return {"status": "updated"}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update nutrition log.")