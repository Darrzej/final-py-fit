from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    age: int
    height: float
    weight: float
    goal: str
    frequency: int
    is_admin: int = 0

class UserLogin(BaseModel):
    username: str
    password: str

class UserDelete(BaseModel):
    user_id: int

class UserUpdate(BaseModel):
    username: str
    age: int
    height: float
    weight: float
    goal: str
    frequency: int
    is_admin: int