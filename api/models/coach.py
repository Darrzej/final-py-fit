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

class ExerciseCreate(BaseModel):
    name: str

class LogUpdate(BaseModel):
    val1: float
    val2: float

