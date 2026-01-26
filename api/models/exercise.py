from pydantic import BaseModel

class WorkoutLog(BaseModel):
    user_id: int
    exercise_id: int
    weight: float
    reps: int
    date: str

class ExerciseAction(BaseModel):
    user_id: int
    exercise_id: int

class ExerciseCreate(BaseModel):
    name: str
    muscle_group: str 

class WorkoutUpdate(BaseModel):
    weight: float
    reps: int

class NutritionUpdate(BaseModel):
    calories: int
    protein: int