from pydantic import BaseModel, EmailStr

class NewUser(BaseModel):
    cognito_id: str
    username: str
    email: EmailStr
