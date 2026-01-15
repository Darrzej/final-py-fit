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

from utils.database import get_user_stats, update_stat, remove_user_exercise

@app.get("/stats/{user_id}")
def get_stats(user_id: int):
    return get_user_stats(user_id).to_dict(orient="records")


@app.post("/stats")
def add_stat(data: dict):
    update_stat(
        data["user_id"],
        data["exercise_id"],
        data["pr"],
        data["reps"],
        data["date"]
    )
    return {"status": "created"}


@app.delete("/exercise/{user_id}/{exercise_id}")
def delete_exercise(user_id: int, exercise_id: int):
    remove_user_exercise(user_id, exercise_id)
    return {"status": "deleted"}


