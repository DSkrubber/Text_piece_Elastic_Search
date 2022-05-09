from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union

from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import RequestError

from .es import MAPPINGS, SETTINGS, es_logger
from .models import TextPiece
from .schemas import (
    TEXT_FIELD_NAMES,
    CountableOperator,
    SearchQuerySchema,
    TextField,
    TextOperator,
    TextPieceOutSchema,
)


def create_index(es_client: Elasticsearch, index_name: int) -> None:
    if not es_client.indices.exists(index=index_name):
        try:
            es_client.indices.create(
                index=index_name, settings=SETTINGS, mappings=MAPPINGS
            )
        except RequestError as error:
            if error.error == "resource_already_exists_exception":
                es_logger.info("Index already exists")
                pass
            else:
                es_logger.error(f"Index creation error: {error}")
                raise error


def delete_old_pieces(
    es_client: Elasticsearch, index_name: int
) -> Optional[Iterator[Dict[str, Union[str, int]]]]:
    es_query = {"query": {"match_all": {}}}  # type: ignore
    objects_to_delete = helpers.scan(
        client=es_client,
        query=es_query,
        index=index_name,
        _source=False,
        track_scores=False,
    )
    for es_object in objects_to_delete:
        es_object["_op_type"] = "delete"
        es_object.pop("_type")
        yield es_object


def index_new_pieces(
    index_name: int, document_pieces: Iterable[TextPiece]
) -> Optional[Iterator[Dict[str, Union[str, int]]]]:
    for text_piece in document_pieces:
        piece_id = text_piece.piece_id
        text_piece_schema = TextPieceOutSchema.from_orm(text_piece)
        yield {
            "_index": index_name,
            "_source": text_piece_schema.dict(),
            "_id": piece_id,
        }


def start_document_indexation(
    es_client: Elasticsearch,
    index_name: int,
    document_pieces: Iterable[TextPiece],
) -> None:
    try:
        helpers.bulk(es_client, delete_old_pieces(es_client, index_name))
    except RequestError as error:
        es_logger.error(f"Error: ElasticSearch clear index error: {error}")
        raise
    try:
        helpers.bulk(es_client, index_new_pieces(index_name, document_pieces))
    except RequestError as error:
        es_logger.error(f"Error: ElasticSearch indexation error: {error}")
        raise


SearchQuery = Dict[str, Union[int, Dict[str, Any]]]
BoolQuery = Dict[str, Dict[str, List[Any]]]


def build_query(request_body: SearchQuerySchema) -> SearchQuery:
    page_num = request_body.pagination.page_num
    page_size = request_body.pagination.page_size
    from_ = (page_num - 1) * page_size
    default_query: dict = {  # type: ignore
        "from": from_,
        "size": page_size,
        "query": {},
        "sort": ["_score", {"created_at": "asc"}],
    }
    query_filters = request_body.filters
    if not query_filters:
        default_query["query"].update({"match_all": {}})
        return default_query
    universal_query: BoolQuery = {"bool": {"must": [], "filter": []}}
    default_query["query"].update(universal_query)
    for query_filter in query_filters:
        field = query_filter.field.value
        operator, value = query_filter.operator.value, query_filter.value
        if field == TextField.indexed:
            value = "true" if value else "false"
        if operator == TextOperator.match:
            default_query["query"]["bool"]["must"].append(
                {"match_phrase": {field: value}}
            )
        elif operator == TextOperator.eq and field in TEXT_FIELD_NAMES:
            default_query["query"]["bool"]["filter"].append(
                {"term": {f"{field}.keyword": value}}
            )
        elif operator == CountableOperator.eq:
            default_query["query"]["bool"]["filter"].append(
                {"term": {field: value}}
            )
        elif operator == CountableOperator.in_:
            default_query["query"]["bool"]["filter"].append(
                ({"terms": {field: value}})
            )
        else:
            default_query["query"]["bool"]["filter"].append(
                {"range": {field: {operator: value}}}
            )
    return default_query


def search_pieces(
    es_client: Elasticsearch, index_name: int, query_body: SearchQuerySchema
) -> Tuple[int, Iterable[Dict[str, Any]]]:
    es_query = build_query(query_body)
    try:
        total = es_client.count(index=str(index_name))["count"]
        data = helpers.scan(
            es_client, query=es_query, index=index_name, preserve_order=True
        )
        return total, data
    except RequestError as error:
        es_logger.error(f"Error: ElasticSearch search error: {error}")
        raise
