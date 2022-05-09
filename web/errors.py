from elasticsearch.exceptions import ApiError, RequestError, TransportError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from .crud import database_logger
from .es import es_logger


def sqlalchemy_exception_handler(
    request: Request, error: SQLAlchemyError
) -> JSONResponse:
    database_logger.error(error)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: SQLAlchemy error ({error})"},
    )


def dbapi_exception_handler(
    request: Request, error: DBAPIError
) -> JSONResponse:
    database_logger.error(error.__cause__)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: DBAPI error ({error.__cause__})"},
    )


def es_transport_exception_handler(
    request: Request, error: TransportError
) -> JSONResponse:
    es_logger.error(error)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: ElasticSearch transport error ({error})"},
    )


def es_api_exception_handler(
    request: Request, error: ApiError
) -> JSONResponse:
    es_logger.error(error)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: ElasticSearch API error ({error})"},
    )


def es_request_exception_handler(
    request: Request, error: RequestError
) -> JSONResponse:
    es_logger.error(error)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: ElasticSearch Request error ({error})"},
    )
