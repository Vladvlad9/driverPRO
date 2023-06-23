from datetime import datetime
from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    user_id: int = Field(ge=1)


class UserInDBSchema(UserSchema):
    id: int = Field(ge=1)
