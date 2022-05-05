import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

ES_HOST = os.environ.get("ES_HOST", "elasticsearch:9200")

APP_HOST = os.environ.get("APP_HOST", "127.0.0.1")
APP_PORT = os.environ.get("APP_PORT", "5000")

POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT")
POSTGRES_DB = os.environ.get("POSTGRES_DB")

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
