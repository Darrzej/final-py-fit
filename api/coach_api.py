from fastapi import FastAPI, HTTPException
from api.models.user import UserCreate, UserLogin, UserUpdate
from api.models.exercise import WorkoutLog, ExerciseAction
from api.models.nutrition import NutritionLog
from api.models.coach import CoachRequest, OneRMRequest
from utils.database import DatabaseManager
import pandas as pd

app = FastAPI()
db = DatabaseManager()

# --- AUTHENTICATION ---
@app.post("/auth/login")
def login(data: UserLogin):
    user = db.get_user(data.username, data.password)
    if not user: 
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "id": user[0], "username": user[1], "age": user[3], 
        "height": user[4], "weight": user[5], "goal": user[6], 
        "frequency": user[7], "is_admin": user[8]
    }

@app.post("/auth/register")
def register(u: UserCreate):
    return db.add_user(u.username, u.password, u.age, u.height, u.weight, u.goal, u.frequency, u.is_admin)

# --- DATA RETRIEVAL ---
@app.get("/data/stats/{user_id}")
def get_stats(user_id: int):
    return db.get_user_stats(user_id).to_dict(orient="records")

@app.get("/data/nutrition/{user_id}")
def get_nutri(user_id: int):
    return db.get_daily_nutrition_summary(user_id).to_dict(orient="records")

@app.get("/exercises/all")
def all_ex():
    return db.get_exercises().to_dict(orient="records")

@app.get("/exercises/user/{user_id}")
def user_ex(user_id: int):
    return db.get_user_exercises(user_id).to_dict(orient="records")

# --- LOGGING & ACTIONS ---
@app.post("/log/workout")
def log_work(d: WorkoutLog):
    return db.update_stat(d.user_id, d.exercise_id, d.weight, d.reps, d.date)

@app.post("/log/nutrition")
def log_nutri(d: NutritionLog):
    return db.add_nutrition_log(d.user_id, d.calories, d.protein, d.date)

@app.post("/exercises/add")
def add_ex(d: ExerciseAction):
    return db.add_user_exercise(d.user_id, d.exercise_id)

@app.post("/exercises/remove")
def rem_ex(d: ExerciseAction):
    return db.remove_user_exercise(d.user_id, d.exercise_id)

# --- DYNAMIC AI COACH ---
@app.post("/coach")
def get_advice(data: CoachRequest):
    advice = []
    
    # Context Setup
    stats_df = pd.DataFrame(data.stats) if data.stats else pd.DataFrame()
    nutri_df = pd.DataFrame(data.nutrition) if data.nutrition else pd.DataFrame()
    goal = data.goal.lower()
    weight = data.weight

    # --- 1. STRENGTH & RECOVERY (Keeping your current feedback) ---
    if not stats_df.empty:
        latest_lifts = stats_df.sort_values('updated_at').groupby('name').last()
        for name, row in latest_lifts.iterrows():
            ratio = row['pr'] / weight
            if ratio < 1.0:
                advice.append({"type": "info", "msg": f"🏋️ **{name}:** Currently {round(ratio,2)}x BW. Focus on 'Linear Progression' (add 2.5kg/session)."})
            elif 1.0 <= ratio < 1.5:
                advice.append({"type": "success", "msg": f"💪 **{name}:** Intermediate level ({round(ratio,2)}x BW). Incorporate 'Pause Reps' for power."})
            else:
                advice.append({"type": "strength", "msg": f"🔥 **{name}:** Elite Status ({round(ratio,2)}x BW). Prioritize CNS recovery."})

    # --- 2. THE NUTRITION STRATEGIST (New Complex Feedback) ---
    if not nutri_df.empty:
        avg_cal = nutri_df['total_calories'].mean()
        avg_prot = nutri_df['total_protein'].mean()
        prot_ratio = avg_prot / weight

        # A. Goal Alignment Check
        if goal == "bulk":
            # Bulking needs weight * 35+ calories
            target = weight * 38
            if avg_cal < (weight * 33):
                advice.append({"type": "warning", "msg": f"🍎 **Caloric Deficit Detected:** Your goal is 'Bulk', but you are averaging {int(avg_cal)} kcal. To grow, you need a surplus. Target: ~{int(target)} kcal."})
            else:
                advice.append({"type": "success", "msg": "✅ **Energy Balance:** Your caloric intake is sufficient for muscular hypertrophy."})
        
        elif goal == "cut":
            # Cutting needs weight * 25- calories
            target = weight * 24
            if avg_cal > (weight * 30):
                advice.append({"type": "warning", "msg": f"📉 **Cut Stalled:** Your calories ({int(avg_cal)}) are too high for fat loss. Aim for {int(target)} kcal to trigger lipolysis."})

        # B. Protein Synthesis Check
        if prot_ratio < 1.8:
            advice.append({"type": "warning", "msg": f"🥩 **Protein Gap:** You're at {round(prot_ratio,1)}g/kg. Your muscles are likely not recovering fully. Reach for 2.0g/kg ({int(weight*2)}g) daily."})
        elif prot_ratio > 2.5:
            advice.append({"type": "info", "msg": "💡 **Protein Saturation:** You are eating very high protein. While safe, you could swap some protein for carbs to increase gym energy."})

    # --- 3. THE "METABOLIC CROSS-CHECK" ---
    if not stats_df.empty and not nutri_df.empty:
        # Check if user is stagnant in strength AND low in calories
        recent_prs = stats_df.tail(3)['pr'].tolist()
        if len(set(recent_prs)) == 1 and goal == "bulk" and prot_ratio < 1.8:
            advice.append({"type": "plateau", "msg": "🛑 **The Recovery Trap:** You've plateaued because your protein and calories are too low for your 'Bulk' goal. The gym isn't the problem—the kitchen is."})

    # --- 4. BIOMETRIC LOGIC ---
    if data.age > 40:
        advice.append({"type": "info", "msg": "🧬 **40+ Biometrics:** Prioritize 8 hours of sleep for hormonal recovery."})

    return {"report": advice}

@app.post("/predict_1rm")
def predict(d: OneRMRequest):
    one_rm = d.weight * (36 / (37 - d.reps)) if d.reps > 1 else d.weight
    return {
        "one_rm": round(one_rm, 1), 
        "zones": {
            "Strength (85%)": round(one_rm*0.85, 1), 
            "Hypertrophy (75%)": round(one_rm*0.75, 1), 
            "Endurance (60%)": round(one_rm*0.6, 1)
        }
    }

# --- ADMIN PANEL ROUTES ---
@app.get("/admin/users")
def get_users():
    return db.get_all_users().to_dict(orient="records")

@app.post("/admin/promote/{user_id}")
def promote(user_id: int):
    return db.promote_user(user_id)

@app.delete("/admin/delete_user/{user_id}")
def delete_user(user_id: int):
    success = db.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "deleted"}

@app.put("/admin/update_user/{user_id}")
def update_user(user_id: int, data: UserUpdate):
    success = db.update_user_details(
        user_id, data.username, data.age, data.height, 
        data.weight, data.goal, data.frequency, data.is_admin
    )
    if not success:
        raise HTTPException(status_code=400, detail="Update failed")
    return {"status": "success"}