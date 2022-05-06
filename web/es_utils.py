from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError

from .es import MAPPINGS, SETTINGS, es_logger


def create_index(es_instance: Elasticsearch, index_name: str) -> None:
    if not es_instance.indices.exists(index=index_name):
        try:
            es_instance.indices.create(
                index=index_name, settings=SETTINGS, mappings=MAPPINGS
            )
        except RequestError as error:
            if error.error == "resource_already_exists_exception":
                es_logger.info("Index already exists")
                pass
            else:
                es_logger.error(f"Index creation error: {error}")
                raise error
