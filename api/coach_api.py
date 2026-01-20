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

class OneRMRequest(BaseModel):
    weight: float
    reps: int

@app.post("/coach")
async def get_coach_advice(data: CoachRequest):
    advice = []
    
    # --- 1. DYNAMIC STRENGTH & RECOVERY TIPS ---
    if data.stats:
        df_stats = pd.DataFrame(data.stats)
        latest_prs = df_stats.groupby('name')['pr'].last()
        
        # Add back the "Specific Tips" based on lifts
        if any("squat" in ex.lower() or "deadlift" in ex.lower() for ex in latest_prs.index):
            advice.append({
                "type": "info", 
                "msg": "🚀 **Recovery Tip:** I see heavy lower-body lifts in your log. Increase calories by 200 today to optimize CNS recovery."
            })
            
        for exercise, pr in latest_prs.items():
            ratio = pr / data.weight
            level = "Novice" if ratio < 1.0 else "Intermediate" if ratio < 1.8 else "Elite"
            advice.append({
                "type": "strength", 
                "msg": f"🏋️ **{exercise}:** Your {round(ratio, 2)}x bodyweight ratio puts you at an **{level}** level. Focus on explosive concentric movement."
            })

    # --- 2. PROGRESSION & PLATEAU LOGIC ---
    if len(data.stats) >= 3:
        df_stats = pd.DataFrame(data.stats)
        recent = df_stats.tail(3)
        if recent['pr'].nunique() == 1:
            advice.append({
                "type": "plateau", 
                "msg": "🛑 **Plateau Alert:** You've hit the same weight 3 times. Try 'Rest-Pause' sets or a 10% deload to break through."
            })
        else:
            advice.append({
                "type": "success", 
                "msg": "📈 **Progress:** Your strength velocity is positive. Stick to the current program; progressive overload is working!"
            })

    # --- 3. NUTRITION & ENERGY ---
    if data.nutrition:
        df_nutri = pd.DataFrame(data.nutrition)
        avg_prot = df_nutri['total_protein'].mean()
        prot_ratio = avg_prot / data.weight
        
        if prot_ratio < 1.6:
            advice.append({
                "type": "warning", 
                "msg": f"⚠️ **Protein Analysis:** You're at {round(prot_ratio,1)}g/kg. To protect muscle mass, aim for {round(data.weight * 1.8)}g total."
            })
        else:
            advice.append({
                "type": "success", 
                "msg": "✅ **Nutrition:** Protein intake is optimal for muscle protein synthesis. Keep hydrating!"
            })

    # --- 4. GENERAL WELLNESS (The "Extra" Tips) ---
    advice.append({
        "type": "info", 
        "msg": "💡 **Pro Tip:** Ensure you are getting 7-8 hours of sleep. Muscle grows while you sleep, not while you're in the gym!"
    })

    return {"report": advice}

@app.post("/predict_1rm")
async def predict_1rm(data: OneRMRequest):
    if data.reps == 1: one_rm = data.weight
    else: one_rm = data.weight * (36 / (37 - data.reps))
    return {
        "one_rm": round(one_rm, 1),
        "zones": {
            "Strength (85%)": round(one_rm * 0.85, 1),
            "Hypertrophy (75%)": round(one_rm * 0.75, 1),
            "Endurance (60%)": round(one_rm * 0.60, 1)
        }
    }