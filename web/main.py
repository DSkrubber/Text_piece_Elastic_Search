from typing import Optional

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ApiError, RequestError, TransportError
from fastapi import Depends, FastAPI, HTTPException, Path, Response, status
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.orm import Session

from .constants import (
    DOCUMENTS_ROUTES,
    ELASTICSEARCH_ROUTES,
    ELASTICSEARCH_TAG,
    ENTITIES_TAG,
    TAGS,
    TEXT_PIECES_ROUTES,
)
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
from .es_utils import create_index, search_pieces, start_document_indexation
from .logger import get_logger
from .models import Document, TextPiece
from .schemas import (
    BadRequestErrorSchema,
    ConnectionErrorSchema,
    DocumentInSchema,
    DocumentOutSchema,
    DocumentPatchSchema,
    NotFoundErrorSchema,
    SearchQuerySchema,
    SearchResultSchema,
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
    summary="Save new document in database and create elasticsearch index.",
)
def post_document(
    document: DocumentInSchema,
    session: Session = Depends(get_db),
    es_client: Optional[Elasticsearch] = Depends(get_es_client),
) -> DocumentOutSchema:
    """Name of saved document should be unique. There will be also index
    created in ElasticSearch to store all related to this document text pieces.
    index_name is equals to created document_id.
    """
    document_db = create_db_entity(session, document, Document)
    main_logger.info(f"Document with '{document.name}' name was created")
    if es_client:
        create_index(es_client, document_db.document_id)
        main_logger.info(f"Index {document_db.document_id} was created")
    return DocumentOutSchema.from_orm(document_db)


@app.get(
    DOCUMENTS_ROUTES + "/{document_id}",
    status_code=status.HTTP_200_OK,
    response_model=DocumentOutSchema,
    responses={
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[ENTITIES_TAG],
    summary="Get document by document_id from database.",
)
def get_document(
    document_id: int = Path(..., example=1), session: Session = Depends(get_db)
) -> DocumentOutSchema:
    document_db = get_db_entity(session, document_id, Document)
    if not document_db:
        error_message = f"Document with id={document_id} was not found."
        main_logger.error(error_message)
        raise HTTPException(status_code=404, detail=error_message)
    return DocumentOutSchema.from_orm(document_db)


@app.patch(
    DOCUMENTS_ROUTES + "/{document_id}",
    response_model=DocumentOutSchema,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": BadRequestErrorSchema},
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[ENTITIES_TAG],
    summary="Update provided fields of document (document_id) in database.",
)
def patch_document(
    new_data: DocumentPatchSchema,
    document_id: int = Path(..., example=1),
    session: Session = Depends(get_db),
) -> DocumentOutSchema:
    """Null as fields value is not allowed."""
    new_data_dict = new_data.dict(exclude_none=True)
    if not new_data_dict:
        error_message = "Wrong request: no data for required field provided."
        main_logger.error(error_message)
        raise HTTPException(status_code=400, detail=error_message)
    document_db = get_db_entity(session, document_id, Document)
    if not document_db:
        error_message = f"Document with id={document_id} was not found."
        main_logger.error(error_message)
        raise HTTPException(status_code=404, detail=error_message)
    patched_document = modify_db_entity(session, document_db, new_data_dict)
    main_logger.info(f"Document with id={document_id} was patched")
    return DocumentOutSchema.from_orm(patched_document)


@app.delete(
    DOCUMENTS_ROUTES + "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[ENTITIES_TAG],
    summary="Delete document by document_id from database.",
)
def delete_document(
    document_id: int = Path(..., example=1),
    session: Session = Depends(get_db),
) -> Response:
    document_db = get_db_entity(session, document_id, Document)
    if not document_db:
        error_message = f"Document with id={document_id} was not found."
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
    status_code=status.HTTP_200_OK,
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


@app.put(
    ELASTICSEARCH_ROUTES + "/{index_name}/index",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": BadRequestErrorSchema},
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[ELASTICSEARCH_TAG],
    summary="Start indexation of all text pieces related to index_name.",
)
def index_document_pieces(
    index_name: int = Path(..., example=1),
    session: Session = Depends(get_db),
    es_client: Optional[Elasticsearch] = Depends(get_es_client),
) -> Response:
    """Index_name equals to document_id. All existing documents for
    "index_name" will be deleted before indexation.
    """
    document_db = get_db_entity(session, index_name, Document)
    if not document_db:
        error_message = f"Document with id={index_name} was not found."
        main_logger.error(error_message)
        raise HTTPException(status_code=404, detail=error_message)
    document_pieces = document_db.text_pieces
    for document_piece in document_pieces:
        document_piece.indexed = True
    start_document_indexation(
        es_client, document_db.document_id, document_pieces
    )
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    ELASTICSEARCH_ROUTES + "/{index_name}/search",
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    tags=[ELASTICSEARCH_TAG],
    summary="Search indexed text pieces for index_name with pagination.",
)
def search_document_pieces(
    query_body: SearchQuerySchema,
    index_name: int = Path(..., example=1),
    es_client: Optional[Elasticsearch] = Depends(get_es_client),
) -> SearchResultSchema:
    """Support pagination (page_num and page_size), if no pagination parameters
    specified - returns first 15 results. In filters you should specify list of
    filters, consists of "field", "operator" and "values". Search for fields:
    "text" and "document_name" (support "match" operator that calculates score
    of relative matching and "eq" that finds exact match of requested string),
    "meta_data" (searches "eq" for values), "type" (has "eq" operator that
    accepts only existing text pieces types), "indexed" (has "eq" and accepts
    only true or false values). Also support search for countable fields:
    "page", "size", and "created_at" with operators: "eq", "in" (array of
    possible values to match) and compare: "gt", "gte", "lt", "lte". If no
    filters provided - returns all documents in index_name. Order results by
    score (if "match" is used) and then by "created_at" timestamp in ascending
    order. Returns pagination parameters (including total number of text pieces
    matching query) and "data" field with list of text pieces.
    """
    if not es_client.indices.exists(index=index_name):
        error_message = f"Index '{index_name}' was not found."
        main_logger.error(error_message)
        raise HTTPException(status_code=404, detail=error_message)
    total, search_result = search_pieces(es_client, index_name, query_body)
    response = {
        "page_num": query_body.pagination.page_num,
        "page_size": query_body.pagination.page_size,
        "total": total,
        "data": [document["_source"] for document in search_result],
    }
    return SearchResultSchema.parse_obj(response)
