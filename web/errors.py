from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from .crud import database_logger


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
