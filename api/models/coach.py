from pydantic import BaseModel
from typing import List, Dict

class CoachRequest(BaseModel):
    username: str
    weight: float
    age: int
    goal: str
    stats: List[Dict]
    nutrition: List[Dict]

class OneRMRequest(BaseModel):
    weight: float
    reps: int