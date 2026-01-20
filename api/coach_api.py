from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import pandas as pd

app = FastAPI()

class CoachRequest(BaseModel):
    username: str
    weight: float
    goal: str
    stats: List[dict]
    nutrition: List[dict]

@app.post("/coach")
async def get_coach_advice(data: CoachRequest):
    advice = []
    
    # --- 1. PERFORMANCE LEVEL ANALYSIS ---
    if data.stats:
        df_stats = pd.DataFrame(data.stats)
        # Calculate Strength-to-Weight Ratio for each lift
        latest_prs = df_stats.groupby('name')['pr'].last()
        
        for exercise, pr in latest_prs.items():
            ratio = pr / data.weight
            level = "Beginner"
            if ratio > 1.2 and exercise.lower() == "bench press": level = "Intermediate"
            if ratio > 2.0 and exercise.lower() == "deadlift": level = "Advanced"
            if ratio > 1.5 and exercise.lower() == "squat": level = "Intermediate"
            
            advice.append({
                "type": "strength",
                "msg": f"🏋️ **{exercise}:** Your ratio is **{round(ratio, 2)}x** bodyweight ({level})."
            })

    # --- 2. RECOVERY & NUTRITION DYNAMICS ---
    if data.nutrition:
        df_nutri = pd.DataFrame(data.nutrition)
        avg_prot = df_nutri['total_protein'].mean()
        avg_cal = df_nutri['total_calories'].mean()
        
        # Calculate Consistency (how many days logged)
        days_logged = len(df_nutri['date'].unique())
        
        if days_logged < 3:
            advice.append({"type": "warning", "msg": "⚠️ **Consistency:** You only have data for " + str(days_logged) + " days. Logging daily improves AI accuracy."})
        
        # Dynamic Calorie Strategy
        if data.goal == "bulk":
            target = (data.weight * 33) + 300 # Rough estimate for bulk
            if avg_cal < target:
                advice.append({"type": "nutrition", "msg": f"🍴 **Caloric Gap:** You're averaging {int(avg_cal)}kcal. To hit your 'Bulk' goal, increase to {int(target)}kcal."})
        
        # Protein quality check
        prot_ratio = avg_prot / data.weight
        if prot_ratio > 2.2:
            advice.append({"type": "info", "msg": "🧬 **Protein:** You are in a 'High Protein' phase (>2.2g/kg). Ensure you're drinking extra water to assist kidney filtration."})
    
    # --- 3. PROGRESSION LOGIC ---
    if len(data.stats) > 3:
        # Check if the last 3 logs for the same exercise are the same (Plateau)
        df_stats['updated_at'] = pd.to_datetime(df_stats['updated_at'])
        recent = df_stats.sort_values('updated_at').tail(3)
        if recent['pr'].nunique() == 1:
            advice.append({"type": "plateau", "msg": "🛑 **Plateau Alert:** Your last 3 sessions show no weight increase. Decrease reps and increase weight by 2.5kg next session."})

    return {"report": advice}