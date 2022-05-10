from datetime import datetime
from enum import Enum
from typing import Dict, Iterable, List, Optional, Union

from pydantic import BaseModel, Field, root_validator


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


class DocumentInSchema(BaseModel):

    name: str = Field(..., min_length=1, example="Interesting book")
    author: str = Field(..., example="John Doe")


class DocumentOutSchema(DocumentInSchema):

    document_id: int = Field(..., example=1)

    class Config:
        orm_mode = True


class DocumentPatchSchema(BaseModel):

    author: Optional[str] = Field(None, example="Jules Verne")


class TextPieceInSchema(BaseModel):

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


class PaginationSchema(BaseModel):
    page_num: Optional[int] = Field(1, example=1)
    page_size: Optional[int] = Field(15, example=15)


class TextField(str, Enum):
    meta_data = "meta_data"
    document_name = "document_name"
    indexed = "indexed"
    type = "type"
    text = "text"


class TextOperator(str, Enum):
    eq = "eq"
    match = "match"


class CountableField(str, Enum):
    piece_id = "piece_id"
    size = "size"
    page = "page"
    created_at = "created_at"


class CountableOperator(str, Enum):
    eq = "eq"
    in_ = "in"
    gt = "gt"
    gte = "gte"
    lt = "lt"
    lte = "lte"


SearchFilterSchemaValue = Union[int, str, List[Union[int, str]]]
TEXT_FIELD_NAMES = TextField.text, TextField.document_name
TYPES_VALUES = TextPieceType.title, TextPieceType.paragraph


class SearchFilterSchema(BaseModel):
    field: Union[TextField, CountableField] = Field(
        ..., example=CountableField.size
    )
    operator: Union[TextOperator, CountableOperator] = Field(
        ..., example=CountableOperator.gt
    )
    value: SearchFilterSchemaValue = Field(..., example=1)

    @root_validator
    def check_text_field_operators(
        cls, values: Dict[str, SearchFilterSchemaValue]
    ) -> Dict[str, SearchFilterSchemaValue]:
        """If field is TextField - operator should not support only Countable
        fields.
        """
        field, operator = values.get("field"), values.get("operator")
        if field in TextField and operator not in TextOperator:
            raise ValueError(
                f"Incompatible operator for text field: {operator}. Use it "
                "with countable fields only."
            )
        return values

    @root_validator
    def check_operator_in_isinstance_list(
        cls, values: Dict[str, SearchFilterSchemaValue]
    ) -> Dict[str, SearchFilterSchemaValue]:
        """Values for "in" operator should be iterables only."""
        op, value = values.get("operator"), values.get("value")
        if op == CountableOperator.in_ and not isinstance(value, Iterable):
            raise ValueError("Value for 'in' operator should be an iterable.")
        return values

    @root_validator
    def check_match_only_text_and_document_name(
        cls, values: Dict[str, SearchFilterSchemaValue]
    ) -> Dict[str, SearchFilterSchemaValue]:
        """Match operator can be provided only for "text" and "document_name"
        fields.
        """
        field, operator = values.get("field"), values.get("operator")
        if field not in TEXT_FIELD_NAMES and operator == TextOperator.match:
            raise ValueError(
                "match can be used with text and document_name fields only."
            )
        return values

    @root_validator
    def check_indexed_boolead(
        cls, values: Dict[str, SearchFilterSchemaValue]
    ) -> Dict[str, SearchFilterSchemaValue]:
        """Indexed field may contain only true or false values"""
        field, value = values.get("field"), values.get("value")
        if field == TextField.indexed and value not in (True, False):
            raise ValueError("Indexed field may contain only true/false value")
        return values

    @root_validator
    def check_type_enum(
        cls, values: Dict[str, SearchFilterSchemaValue]
    ) -> Dict[str, SearchFilterSchemaValue]:
        """Type field may contain only title or paragraph values"""
        field, value = values.get("field"), values.get("value")
        if field == TextField.type and value not in TYPES_VALUES:
            raise ValueError("Type may be either 'title' or 'paragraph' only")
        return values


class SearchQuerySchema(BaseModel):
    pagination: Optional[PaginationSchema]
    filters: Optional[List[SearchFilterSchema]]


class SearchResultSchema(BaseModel):
    page_num: int = Field(..., example=1)
    page_size: int = Field(..., example=15)
    total: int = Field(..., example=100)
    data: List[TextPieceOutSchema]
