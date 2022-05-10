from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from .database import Base
from .logger import get_logger
from .models import Document, TextPiece
from .schemas import DocumentInSchema, TextPieceInSchema

database_logger = get_logger(__name__)


def create_db_entity(
    session: Session,
    entity: Union[DocumentInSchema, TextPieceInSchema],
    model: Base,
    **kwargs: int,
) -> Union[Document, TextPiece]:
    """Creates entity in db table for model from provided schema.

    :param session: SQLAlchemy session connected to database.
    :param entity: pydantic schema with entity data.
    :param model: ORM model associated with database table.
    :param kwargs: additional parameters for new database entity.
    :return: new created database row entity.
    """
    entity_db: Union[Document, TextPiece] = model(**entity.dict(), **kwargs)
    session.add(entity_db)
    session.commit()
    session.refresh(entity_db)
    return entity_db


def get_db_entity(
    session: Session, entity_id: Union[int, str], model: Base
) -> Optional[Union[Document, TextPiece]]:
    """Get entity in db table for model with provided Primary Key.

    :param session: SQLAlchemy session connected to database.
    :param entity_id: PK value to search for.
    :param model: ORM model associated with database table.
    :return: database row entity.
    """
    entity_db: Union[Document, TextPiece] = session.query(model).get(entity_id)
    return entity_db


def modify_db_entity(
    session: Session,
    entity_db: Union[Document, TextPiece],
    patch_data: Dict[str, Any],
) -> Union[Document, TextPiece]:
    """Updates provided row entity with parameters from patch_data.

    :param session: SQLAlchemy session connected to database.
    :param entity_db: database row entity.
    :param patch_data: key-value dict with entity fields parameters to update.
    :return: updated database row entity.
    """
    for field, new_value in patch_data.items():
        setattr(entity_db, field, new_value)
    session.commit()
    return entity_db


def delete_db_entity(
    session: Session, entity_db: Union[Document, TextPiece]
) -> None:
    """Delete entity with provided Primary Key from db model's table.

    :param session: SQLAlchemy session connected to database.
    :param entity_db: PK value to search for.
    :return: None.
    """
    session.delete(entity_db)
    session.commit()
