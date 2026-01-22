from pydantic import BaseModel

class NutritionLog(BaseModel):
    user_id: int
    calories: int
    protein: int
    date: str