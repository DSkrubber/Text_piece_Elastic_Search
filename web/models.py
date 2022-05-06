from sqlalchemy import CheckConstraint, Column, ForeignKey, func
from sqlalchemy.dialects.postgresql import (
    BOOLEAN,
    ENUM,
    INTEGER,
    JSONB,
    TEXT,
    VARCHAR,
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP

from .database import Base
from .schemas import TextPieceType


class Document(Base):  # type: ignore
    __tablename__ = "documents"

    document_id = Column(INTEGER, primary_key=True)
    name = Column(VARCHAR, nullable=False, unique=True)
    author = Column(VARCHAR, nullable=False, index=True)
    text_pieces = relationship(
        "TextPiece",
        back_populates="document",
        cascade="all, delete, delete-orphan",
    )


class TextPiece(Base):  # type: ignore
    __tablename__ = "text_pieces"

    piece_id = Column(INTEGER, primary_key=True)
    meta_data = Column(JSONB, nullable=True)
    indexed = Column(BOOLEAN, nullable=False, default=False)
    document_name = Column(
        VARCHAR, ForeignKey("documents.name"), nullable=False, index=True
    )
    size = Column(INTEGER, nullable=False, index=True)
    type = Column(ENUM(TextPieceType), nullable=False)
    page = Column(
        INTEGER,
        CheckConstraint("page > 1", name="positive_page"),
        nullable=False,
    )
    text = Column(TEXT, nullable=False)
    created_at = Column(
        TIMESTAMP, server_default=func.now(), nullable=False, index=True
    )
    document = relationship("Document", back_populates="text_pieces")
