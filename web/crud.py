from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from .database import Base
from .logger import get_logger
from .models import Document, TextPiece
from .schemas import DocumentSchema, TextPieceInSchema

database_logger = get_logger(__name__)


def create_db_entity(
    session: Session,
    entity: Union[DocumentSchema, TextPieceInSchema],
    model: Base,
    **kwargs: int,
) -> Union[Document, TextPiece]:
    entity_db: Union[Document, TextPiece] = model(**entity.dict(), **kwargs)
    session.add(entity_db)
    session.commit()
    session.refresh(entity_db)
    return entity_db


def get_db_entity(
    session: Session, entity_id: Union[int, str], model: Base
) -> Optional[Union[Document, TextPiece]]:
    entity_db: Union[Document, TextPiece] = session.query(model).get(entity_id)
    return entity_db


def modify_db_entity(
    session: Session,
    entity_db: Union[Document, TextPiece],
    patch_data: Dict[str, Any],
) -> Union[Document, TextPiece]:
    for field, new_value in patch_data.items():
        setattr(entity_db, field, new_value)
    session.commit()
    return entity_db


def delete_db_entity(
    session: Session, entity_db: Union[Document, TextPiece]
) -> None:
    session.delete(entity_db)
    session.commit()
