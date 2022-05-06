from elasticsearch.exceptions import ApiError, RequestError, TransportError
from fastapi import Depends, FastAPI, HTTPException, Path, Response, status
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.orm import Session

from .constants import DOCUMENTS_ROUTES, ENTITIES_TAG, TAGS, TEXT_PIECES_ROUTES
from .crud import (
    create_db_entity,
    delete_db_entity,
    get_db_entity,
    modify_db_entity,
)
from .database import get_db
from .errors import (
    dbapi_exception_handler,
    es_api_exception_handler,
    es_request_exception_handler,
    es_transport_exception_handler,
    sqlalchemy_exception_handler,
)
from .es import get_es_client
from .es_utils import create_index
from .logger import get_logger
from .models import Document, TextPiece
from .schemas import (
    BadRequestErrorSchema,
    ConnectionErrorSchema,
    DocumentInSchema,
    DocumentOutSchema,
    DocumentPatchSchema,
    NotFoundErrorSchema,
    TextPieceInSchema,
    TextPieceOutSchema,
    TextPiecePatchSchema,
)

app = FastAPI(
    title="Text pieces indexation and search",
    version="0.1.0",
    openapi_tags=TAGS,
)

app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(DBAPIError, dbapi_exception_handler)
app.add_exception_handler(TransportError, es_transport_exception_handler)
app.add_exception_handler(ApiError, es_api_exception_handler)
app.add_exception_handler(RequestError, es_request_exception_handler)

main_logger = get_logger(__name__)


@app.on_event("startup")
async def startup_event() -> None:
    get_es_client()


@app.on_event("shutdown")
async def app_shutdown() -> None:
    es_client = get_es_client()
    es_client.close()


@app.post(
    DOCUMENTS_ROUTES,
    status_code=status.HTTP_201_CREATED,
    response_model=DocumentOutSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[ENTITIES_TAG],
    summary="Save new document in database.",
)
def post_document(
    document: DocumentInSchema, session: Session = Depends(get_db)
) -> DocumentOutSchema:
    """Name of saved document should be unique. There will be also index
    created in ElasticSearch to store all related to this document text pieces.
    """
    document_db = create_db_entity(session, document, Document)
    main_logger.info(f"Document with '{document.name}' name was created")
    es_client = get_es_client()
    if es_client:
        create_index(es_client, document_db.document_id)
        main_logger.info(f"Index {document_db.document_id} was created")
    return DocumentOutSchema.from_orm(document_db)


@app.get(
    DOCUMENTS_ROUTES + "/{document_name}",
    status_code=status.HTTP_200_OK,
    response_model=DocumentOutSchema,
    responses={
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[ENTITIES_TAG],
    summary="Get document by name from database.",
)
def get_document(
    document_name: str = Path(..., example="Interesting book"),
    session: Session = Depends(get_db),
) -> DocumentOutSchema:
    document_db = get_db_entity(session, document_name, Document)
    if not document_db:
        error_message = f"Document with '{document_name}' name was not found."
        main_logger.error(error_message)
        raise HTTPException(status_code=404, detail=error_message)
    return DocumentOutSchema.from_orm(document_db)


@app.patch(
    DOCUMENTS_ROUTES + "/{document_name}",
    response_model=DocumentOutSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[ENTITIES_TAG],
    summary="Update provided fields of document (document_name) in database.",
)
def patch_document(
    new_data: DocumentPatchSchema,
    document_name: str = Path(..., example="Interesting book"),
    session: Session = Depends(get_db),
) -> DocumentOutSchema:
    """Null as fields value is not allowed."""
    new_data_dict = new_data.dict(exclude_none=True)
    if not new_data_dict:
        error_message = "Wrong request: no data for required field provided."
        main_logger.error(error_message)
        raise HTTPException(status_code=400, detail=error_message)
    document_db = get_db_entity(session, document_name, Document)
    if not document_db:
        error_message = f"Document with '{document_name}' name was not found."
        main_logger.error(error_message)
        raise HTTPException(status_code=404, detail=error_message)
    patched_document = modify_db_entity(session, document_db, new_data_dict)
    main_logger.info(f"Document with '{document_db.name} name was patched")
    return DocumentOutSchema.from_orm(patched_document)


@app.delete(
    DOCUMENTS_ROUTES + "/{document_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[ENTITIES_TAG],
    summary="Delete document by name from database.",
)
def delete_document(
    document_name: str = Path(..., example="Interesting book"),
    session: Session = Depends(get_db),
) -> Response:
    document_db = get_db_entity(session, document_name, Document)
    if not document_db:
        error_message = f"Document with '{document_name}' name was not found."
        main_logger.error(error_message)
        raise HTTPException(status_code=404, detail=error_message)
    delete_db_entity(session, document_db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    TEXT_PIECES_ROUTES,
    status_code=status.HTTP_201_CREATED,
    response_model=TextPieceOutSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[ENTITIES_TAG],
    summary="Save new text piece in database.",
)
def post_text_piece(
    text_piece: TextPieceInSchema, session: Session = Depends(get_db)
) -> TextPieceOutSchema:
    """Document with document_name must exist in database to save related
    text_piece. Only meta_data field is optional.
    """
    text_piece_db = create_db_entity(
        session, text_piece, TextPiece, size=len(text_piece.text)
    )
    main_logger.info(f"Document with '{text_piece_db.piece_id} was created")
    return TextPieceOutSchema.from_orm(text_piece_db)


@app.get(
    TEXT_PIECES_ROUTES + "/{piece_id}",
    status_code=status.HTTP_200_OK,
    response_model=TextPieceOutSchema,
    responses={
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[ENTITIES_TAG],
    summary="Get text piece by piece_id from database.",
)
def get_text_piece(
    piece_id: int = Path(..., example=1), session: Session = Depends(get_db)
) -> TextPieceOutSchema:
    text_piece_db = get_db_entity(session, piece_id, TextPiece)
    if not text_piece_db:
        error_message = f"Text piece with id={piece_id} was not found."
        main_logger.error(error_message)
        raise HTTPException(status_code=404, detail=error_message)
    return TextPieceOutSchema.from_orm(text_piece_db)


@app.patch(
    TEXT_PIECES_ROUTES + "/{piece_id}",
    response_model=TextPieceOutSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[ENTITIES_TAG],
    summary="Update provided fields of text_piece (piece_id) in database.",
)
def patch_text_piece(
    new_data: TextPiecePatchSchema,
    piece_id: int = Path(..., example=1),
    session: Session = Depends(get_db),
) -> TextPieceOutSchema:
    """Null as fields value allowed only for meta_data."""
    new_data_unset_excluded = new_data.dict(exclude_unset=True)
    with_meta_data = "meta_data" in new_data_unset_excluded
    new_data_dict = new_data.dict(exclude_none=True)
    if not (new_data_dict or with_meta_data):
        error_message = "Wrong request: no data for required field provided."
        main_logger.error(error_message)
        raise HTTPException(status_code=400, detail=error_message)
    if "text" in new_data_dict:
        new_data_dict["size"] = len(new_data_dict["text"])
    if with_meta_data and not new_data_unset_excluded["meta_data"]:
        new_data_dict["meta_data"] = None
    text_piece_db = get_db_entity(session, piece_id, TextPiece)
    if not text_piece_db:
        error_message = f"Text piece with id={piece_id} was not found."
        main_logger.error(error_message)
        raise HTTPException(status_code=404, detail=error_message)
    patched_document = modify_db_entity(session, text_piece_db, new_data_dict)
    main_logger.info(f"Document with id={text_piece_db.piece_id} was patched")
    return TextPieceOutSchema.from_orm(patched_document)


@app.delete(
    TEXT_PIECES_ROUTES + "/{piece_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[ENTITIES_TAG],
    summary="Delete text piece by piece_id from database.",
)
def delete_text_piece(
    piece_id: int = Path(..., example=1),
    session: Session = Depends(get_db),
) -> Response:
    text_piece_db = get_db_entity(session, piece_id, TextPiece)
    if not text_piece_db:
        error_message = f"Text piece with id={piece_id} was not found."
        main_logger.error(error_message)
        raise HTTPException(status_code=404, detail=error_message)
    delete_db_entity(session, text_piece_db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
