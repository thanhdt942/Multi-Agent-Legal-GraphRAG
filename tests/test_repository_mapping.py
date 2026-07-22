from legal_graph.application.services import PROPOSED_WARNING, SOURCE_METADATA_WARNING
from legal_graph.infrastructure.neo4j_repository import public_node, relationship_data


def test_public_node_removes_vectors_and_maps_parent() -> None:
    result = public_node(
        {
            "id": "n1",
            "parent_key": "p1",
            "content": "source",
            "embedding": [0.1],
            "comparison_embedding": [0.2],
            "embedding_text": "internal",
        }
    )
    assert result == {"id": "n1", "content": "source", "parent_id": "p1"}


def test_proposed_relationship_always_warns() -> None:
    result = relationship_data(
        {
            "type": "SUA_DOI",
            "source_id": "a",
            "target_id": "b",
            "properties": {"status": "PROPOSED"},
        }
    )
    assert PROPOSED_WARNING in result["warnings"]


def test_statusless_source_relationship_stays_null_and_warns() -> None:
    result = relationship_data(
        {
            "type": "THAY_THE",
            "source_id": "a",
            "target_id": "b",
            "properties": {},
        }
    )
    assert result["status"] is None
    assert SOURCE_METADATA_WARNING in result["warnings"]
