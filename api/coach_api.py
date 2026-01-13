from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from models.coach import Coach
from models.user import User

app = FastAPI(title="FitAI Coach API")

class CoachRequest(BaseModel):
    user: dict
    stats: list

@app.post("/coach")
def coach_report(data: CoachRequest):
    user_data = data.user
    user = User(
        id=user_data["id"],
        username=user_data["username"],
        age=user_data["age"],
        height=user_data["height"],
        weight=user_data["weight"],
        goal=user_data["goal"],
        frequency=user_data["frequency"]
    )

    stats_df = pd.DataFrame(data.stats)
    coach = Coach(user, stats_df)
    feedback = coach.analyze()

    return {"report": feedback}

