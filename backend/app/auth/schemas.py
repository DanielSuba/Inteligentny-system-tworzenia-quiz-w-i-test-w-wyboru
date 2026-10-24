from typing import Literal

from pydantic import BaseModel, EmailStr, Field

Locale = Literal["pl", "en"]
Password = Field(min_length=10, max_length=128)
Username = Field(pattern=r"^[A-Za-z0-9_]{3,24}$")


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Password
    username: str = Username
    displayName: str | None = Field(default=None, min_length=1, max_length=50)
    locale: Locale = "pl"


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class EmailIn(BaseModel):
    email: EmailStr


class TokenIn(BaseModel):
    token: str = Field(max_length=200)


class ResetIn(BaseModel):
    token: str = Field(max_length=200)
    password: str = Password


class StatusOut(BaseModel):
    status: str
