from pydantic import BaseModel, EmailStr

class RegistrationData(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginData(BaseModel):
    username: str
    password: str
