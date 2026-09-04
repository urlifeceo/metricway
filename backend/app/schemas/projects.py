from pydantic import BaseModel, field_validator


class ProjectCreateRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not (1 <= len(value) <= 64):
            raise ValueError("name must be 1-64 characters")
        return value


class ProjectOut(BaseModel):
    project_token: str
    name: str
