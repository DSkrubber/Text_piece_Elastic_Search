import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


APP_HOST = os.environ.get("APP_HOST")
APP_PORT = os.environ.get("APP_PORT")

POSTGRES_USER = os.environ.get("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "admin")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", 5432)
POSTGRES_DB = os.environ.get("POSTGRES_DB", "postgres")

DOCUMENTS_ROUTES = "/documents"
TEXT_PIECES_ROUTES = "/text_pieces"

ENTITIES_TAG = "Documents and text pieces"
ELASTICSEARCH_TAG = "Elasticsearch"
TAGS = [
    {
        "name": ENTITIES_TAG,
        "description": "CRUD actions associated with database entities.",
    },
    {
        "name": ELASTICSEARCH_TAG,
        "description": "Elasticsearch indexation and search.",
    },
]
