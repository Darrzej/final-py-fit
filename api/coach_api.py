from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from utils.analysis import recommend_next_workout

app = FastAPI(title="FitAI Coach API")

class WorkoutData(BaseModel):
    workouts: list

@app.get("/")
def root():
    return {"message": "Welcome to FitAI Coach API"}

@app.post("/recommend")
def get_recommendation(data: WorkoutData):
    df = pd.DataFrame(data.workouts)
    message = recommend_next_workout(df)
    return {"recommendation": message}
