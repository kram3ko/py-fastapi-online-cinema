from datetime import date

from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, HttpUrl, ValidationInfo, field_validator
from starlette import status

from validation import validate_birth_date, validate_gender, validate_image, validate_name


class ProfileCreateRequestSchema(BaseModel):
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date
    info: str
    avatar: UploadFile

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_field(cls, name: str, info: ValidationInfo) -> str:
        try:
            validate_name(name)
            return name.lower()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[{"type": "value_error", "loc": [info.field_name], "msg": str(e), "input": name}],
            )

    @field_validator("avatar")
    @classmethod
    def validate_avatar_field(cls, avatar: UploadFile, info: ValidationInfo) -> UploadFile:
        try:
            validate_image(avatar)
            return avatar
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[{"type": "value_error", "loc": [info.field_name], "msg": str(e), "input": avatar.filename}],
            )

    @field_validator("gender")
    @classmethod
    def validate_gender_field(cls, gender: str, info: ValidationInfo) -> str:
        try:
            validate_gender(gender)
            return gender
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[{"type": "value_error", "loc": [info.field_name], "msg": str(e), "input": gender}],
            )

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth_field(cls, date_of_birth: date, info: ValidationInfo) -> date:
        try:
            validate_birth_date(date_of_birth)
            return date_of_birth
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[{"type": "value_error", "loc": [info.field_name], "msg": str(e), "input": str(date_of_birth)}],
            )

    @field_validator("info")
    @classmethod
    def validate_info_field(cls, info: str, info_field: ValidationInfo) -> str:
        cleaned_info = info.strip()
        if not cleaned_info:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[
                    {
                        "type": "value_error",
                        "loc": [info_field.field_name],
                        "msg": "Info field cannot be empty or contain only spaces.",
                        "input": info,
                    }
                ],
            )
        return cleaned_info


class ProfileResponseSchema(BaseModel):
    id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    info: str | None = None
    avatar: HttpUrl | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": [
                {
                    "id": 1,
                    "first_name": "John",
                    "last_name": "Doe",
                    "gender": "male",
                    "date_of_birth": "1990-01-01",
                    "info": "Some info",
                    "avatar": "https://example.com/avatar.jpg"
                }
            ]
        }
    )
