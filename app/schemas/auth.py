from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    is_active: bool
    telegram_chat_id: str | None

class Token(BaseModel):
    access_token: str
    token_type: str
