from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import pandas as pd
from models.coach import Coach
from models.user import User as UserModel

app = FastAPI(title="FitAI Professional API")

# --- Pydantic Schemas ---
class UserSchema(BaseModel):
    id: int
    username: str
    age: int
    height: float
    weight: float
    goal: str
    frequency: int

class CoachRequest(BaseModel):
    user: UserSchema
    stats: List[Dict]

# --- Endpoints ---
@app.post("/coach")
def coach_report(data: CoachRequest):
    user_data = data.user.dict()
    
    # Instantiate User Object (OOP)
    user_obj = UserModel(
        id=user_data["id"],
        username=user_data["username"],
        age=user_data["age"],
        height=user_data["height"],
        weight=user_data["weight"],
        goal=user_data["goal"],
        frequency=user_data["frequency"]
    )

    stats_df = pd.DataFrame(data.stats)
    
    # Logic now resides purely in the Coach model based on user metrics
    coach = Coach(user_obj, stats_df)
    feedback = coach.analyze()

    return {"report": feedback}

@app.get("/health")
def health():
    return {"status": "online"}