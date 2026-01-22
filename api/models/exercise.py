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