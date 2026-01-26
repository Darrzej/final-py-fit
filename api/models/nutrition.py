from pydantic import BaseModel

class NutritionLog(BaseModel):
    user_id: int
    calories: int
    protein: int
    date: str

class WorkoutUpdate(BaseModel):
    weight: float
    reps: int

class NutritionUpdate(BaseModel):
    calories: int
    protein: int