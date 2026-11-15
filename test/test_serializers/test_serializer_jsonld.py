from __future__ import annotations

import json
import logging
import pprint
from typing import Any, Union

import pytest

from rdflib import BNode, ConjunctiveGraph, Dataset, Graph
from rdflib.compare import isomorphic
from rdflib.plugins.shared.jsonld.context import Context
from test.utils.namespace import EGDO


@pytest.mark.parametrize(
    ["input"],
    [
        (
            Context(
                {
                    "eg": f"{EGDO}",
                }
            ),
        ),
        ({"eg": f"{EGDO}"},),
    ],
)
def test_serialize_context(input: Union[dict[str, Any], Context]) -> None:
    """
    The JSON-LD serializer accepts and correctly serializes the context argument to the output.
    """
    graph = Graph()
    graph.add((EGDO.subject, EGDO.predicate, EGDO.object0))
    graph.add((EGDO.subject, EGDO.predicate, EGDO.object1))
    context = Context(
        {
            "eg": f"{EGDO}",
        }
    )
    logging.debug("context = %s", pprint.pformat(vars(context)))
    data = graph.serialize(format="json-ld", context=context)
    logging.debug("data = %s", data)
    obj = json.loads(data)
    assert obj["@context"] == {"eg": f"{EGDO}"}


def test_serialize_dataset_keeps_blank_node_named_graphs() -> None:
    """
    Serializing a Dataset to JSON-LD must not modify the dataset, and graphs
    named with a blank node must be kept as named graphs instead of being
    merged into the default graph.
    """
    dataset = Dataset()
    dataset.add((EGDO.subject, EGDO.predicate, EGDO.object0))
    named_graph = dataset.graph(BNode("g1"))
    named_graph.add((EGDO.subject, EGDO.predicate, EGDO.object1))

    quads_before = set(dataset.quads())
    data = dataset.serialize(format="json-ld")
    assert set(dataset.quads()) == quads_before, "serialize modified the dataset"

    obj = json.loads(data)
    named_nodes = [
        node
        for node in obj
        if isinstance(node, dict) and node.get("@id", "").startswith("_:")
    ]
    assert len(named_nodes) == 1
    assert "@graph" in named_nodes[0]

    roundtrip = Dataset()
    roundtrip.parse(data=data, format="json-ld")
    assert isomorphic(dataset, roundtrip)
    assert any(
        isinstance(graph.identifier, BNode) and len(graph) > 0
        for graph in roundtrip.graphs()
    )


def test_serialize_dataset_is_not_modified_with_only_unnamed_content() -> None:
    """Serializing a Dataset must not modify it, even without named graphs."""
    dataset = Dataset()
    dataset.add((EGDO.subject, EGDO.predicate, EGDO.object0))

    quads_before = set(dataset.quads())
    dataset.serialize(format="json-ld")
    assert set(dataset.quads()) == quads_before, "serialize modified the dataset"


def test_serialize_conjunctive_graph_still_merges_unnamed_contexts() -> None:
    """
    A plain ConjunctiveGraph keeps the old behaviour: unnamed (blank node
    identified) contexts are merged into the default graph on output.
    """
    conjunctive_graph = ConjunctiveGraph()
    context = conjunctive_graph.get_context(BNode("g1"))
    context.add((EGDO.subject, EGDO.predicate, EGDO.object0))

    data = conjunctive_graph.serialize(format="json-ld")
    obj = json.loads(data)
    assert isinstance(obj, list)
    assert all("@graph" not in node for node in obj)

    graph = Graph().parse(data=data, format="json-ld")
    assert (EGDO.subject, EGDO.predicate, EGDO.object0) in graph
