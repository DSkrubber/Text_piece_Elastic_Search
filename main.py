from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from elasticsearch import Elasticsearch
from fastapi import Body, FastAPI
from pydantic import BaseModel, validator

es = Elasticsearch(hosts="elasticsearch:9200")
# es = Elasticsearch(hosts="localhost:9200")
app = FastAPI()


class TextPiece(BaseModel):
    text: str = "Some default text for testing functionality."
    piece_id: Optional[UUID] = uuid4()
    type: str
    page_number: int
    document_name: str
    timestamp: Optional[datetime] = datetime.now()

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


examples = {
    "passing_1": {
        "summary": "First normal example",
        "value": {
            "text": "Some default text for testing functionality.",
            "type": "title",
            "page_number": 0,
            "document_name": "doc.pdf",
        },
    },
    "passing_2": {
        "summary": "Second normal example",
        "value": {
            "text": "Another text for testing functionality.",
            "piece_id": "12345d1d-5fca-4ae2-a4d4-fa1d1ce0d111",
            "type": "paragraph",
            "page_number": 1,
            "document_name": "another_doc.pdf",
        },
    },
    "invalid": {
        "summary": "Invalid values example",
        "value": {
            "text": "This will be failure case.",
            "type": "wrong type",
            "page_number": 2,
            "document_name": "doc.notpdf",
        },
    },
}

query = {"match": {"text": "Some"}}


@app.put("/send")
async def add_item(*, item: TextPiece = Body(..., examples=examples)):
    doc = item.json()
    res = es.index(index="job_id", id=item.piece_id, document=doc)
    return res


@app.get("/load")
def get_item():
    res = es.search(index="job_id", _source=False, query=query)
    return res
