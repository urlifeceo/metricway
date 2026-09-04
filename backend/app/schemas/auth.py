from pydantic import BaseModel, field_validator


class RegisterRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()
        if not (3 <= len(value) <= 32):
            raise ValueError("username must be 3-32 characters")
        if not all(c.isalnum() or c in "._-" for c in value):
            raise ValueError("username can contain letters, digits, '.', '_' and '-' only")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("password must be at least 8 characters")
        return value
