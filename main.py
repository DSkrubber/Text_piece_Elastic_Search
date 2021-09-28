from json import loads
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, validator

DB = {}
app = FastAPI()


class TextPiece(BaseModel):
    text: str = "Some default text for testing functionality."
    piece_id: Optional[str] = str(uuid4())
    type: str
    page_number: int
    document_name: str

    @validator("type")
    def possible_content_type(cls, value: str):
        if value not in ("paragraph", "title"):
            raise ValueError("must be either paragraph or title")
        return value

    @validator("document_name")
    def is_pdf(cls, name: str):
        if not name.endswith(".pdf"):
            raise ValueError("provide pdf document name, including extension")
        return name


@app.get("/pieces/{piece_id}")
async def read_root(piece_id: str):
    return loads(DB[piece_id].json())


@app.put("/pieces")
async def update_item(piece: TextPiece):
    global DB
    DB[piece.piece_id] = piece
    return loads(piece.json())
