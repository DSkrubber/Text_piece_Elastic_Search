from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ConnectionErrorSchema(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "Error: Connection error."},
        }


class NotFoundErrorSchema(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "Error: Resource was not found."},
        }


class BadRequestErrorSchema(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "Error: Bad request."},
        }


class TextPieceType(str, Enum):
    title = "title"  # type: ignore
    paragraph = "paragraph"


class DocumentSchema(BaseModel):
    """Declares fields for document object"""

    name: str = Field(..., min_length=1, example="Interesting book")
    author: str = Field(..., example="John Doe")

    class Config:
        orm_mode = True


class DocumentPatchSchema(BaseModel):
    """Declares fields for document object"""

    author: Optional[str] = Field(None, example="Jules Verne")


class TextPieceInSchema(BaseModel):
    """Declares fields for text piece object"""

    text: str = Field(
        ..., min_length=1, example="Some text for testing functionality."
    )
    type: TextPieceType = Field(
        ..., description="Must be paragraph or title", example="title"
    )
    page: int = Field(
        ..., gt=0, description="Must be positive number", example=1
    )
    document_name: str = Field(
        ...,
        min_length=1,
        description="Must be already saved in database",
        example="Interesting book",
    )
    meta_data: Optional[dict] = Field(  # type: ignore
        None, example={"property": "value"}
    )


class TextPieceOutSchema(TextPieceInSchema):
    piece_id: int = Field(..., example=1)
    indexed: bool = Field(..., example=False)
    size: int = Field(..., example=1024)
    created_at: datetime = Field(..., example="2021-10-19 01:01:01")

    class Config:
        orm_mode = True


class TextPiecePatchSchema(BaseModel):
    """Declares fields for text piece object"""

    text: Optional[str] = Field(
        None, min_length=1, example="Some text for testing functionality."
    )
    type: Optional[TextPieceType] = Field(
        None, description="Must be paragraph or title", example="title"
    )
    page: Optional[int] = Field(
        None, gt=0, description="Must be positive number", example=1
    )
    document_name: Optional[str] = Field(
        None,
        min_length=1,
        description="Must be already saved in database",
        example="Interesting book",
    )
    meta_data: Optional[dict] = Field(  # type: ignore
        None, example={"property": "value"}
    )
