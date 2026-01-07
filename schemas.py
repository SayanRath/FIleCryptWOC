from pydantic import BaseModel

# What we need when a user signs up
class UserCreate(BaseModel):
    name: str
    email: str
    password: str





# What we show when someone views a profile (No password included!)
class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True