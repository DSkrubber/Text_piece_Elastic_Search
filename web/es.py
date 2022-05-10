from typing import List

from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import ApiError, TransportError

from .constants import ES_HOST, ES_PORT
from .logger import get_logger

es_logger = get_logger(__name__)

SETTINGS = {
    "analysis": {
        "analyzer": {
            "standard_with_stop": {
                "type": "standard",
                "stopwords": "_english_",
                "tokenizer": "lowercase",
            },
        },
    },
    "index": {
        "blocks": {
            "read_only_allow_delete": "false",
        },
    },
}
MAPPINGS = {
    "properties": {
        "piece_id": {
            "type": "unsigned_long",
            "index": "false",
        },
        "meta_data": {
            "type": "flattened",
        },
        "indexed": {
            "type": "boolean",
        },
        "document_name": {
            "type": "text",
            "analyzer": "standard",
            "fields": {
                "keyword": {
                    "type": "keyword",
                },
            },
        },
        "size": {
            "type": "unsigned_long",
        },
        "type": {
            "type": "keyword",
        },
        "page": {
            "type": "unsigned_long",
        },
        "text": {
            "type": "text",
            "analyzer": "standard_with_stop",
            "fields": {
                "keyword": {
                    "type": "keyword",
                }
            },
        },
        "created_at": {
            "type": "date",
            "format": "strict_date_optional_time_nanos",
        },
    },
}
ES_URL = f"{ES_HOST}:{ES_PORT}"

ES_CLIENTS: List[AsyncElasticsearch] = []


async def get_es_client() -> AsyncElasticsearch:
    if not ES_CLIENTS:
        try:
            ES_CLIENTS.append(AsyncElasticsearch(hosts=ES_URL))
            es_logger.info("ElasticSearch client connected successfully")
        except (TransportError, ApiError) as error:
            es_logger.error(f"Error: ElasticSearch connection error: {error}")
            raise
    return ES_CLIENTS[0]
