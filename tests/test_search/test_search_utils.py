from dataclasses import dataclass

from bigdata_research_tools.search import search_utils


@dataclass
class FakeSdkEntity:
    id: str
    name: str
    entity_type: str = "COMP"


@dataclass
class MalformedSdkEntity:
    name: str
    entity_type: str = "COMP"


class FakeKnowledgeGraph:
    def get_entities(self, ids: list[str]) -> list[FakeSdkEntity | MalformedSdkEntity]:
        return [
            FakeSdkEntity(id=ids[0], name="Valid Company"),
            MalformedSdkEntity(name="Malformed Company"),
        ]


class FakeBigdata:
    knowledge_graph = FakeKnowledgeGraph()


def test_lookup_entities_skips_malformed_sdk_entities(monkeypatch) -> None:
    monkeypatch.setattr(search_utils, "bigdata_connection", lambda: FakeBigdata())

    entities = search_utils._look_up_entities_binary_search(["ABC123", "DEF456"])

    assert len(entities) == 1
    assert entities[0].id == "ABC123"
    assert entities[0].name == "Valid Company"
