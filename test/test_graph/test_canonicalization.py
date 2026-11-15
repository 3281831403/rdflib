from collections import Counter
from io import StringIO
from typing import TYPE_CHECKING

import pytest

import rdflib
from rdflib import (
    RDF,
    BNode,
    ConjunctiveGraph,
    Dataset,
    Graph,
    Literal,
    Namespace,
    URIRef,
)
from rdflib.compare import isomorphic, to_canonical_graph, to_isomorphic
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID
from rdflib.namespace import FOAF
from rdflib.plugins.stores.memory import Memory
from test.utils import GraphHelper

if TYPE_CHECKING:
    from rdflib.graph import _TripleType


def get_digest_value(rdf, mimetype):
    graph = Graph()
    graph.parse(StringIO(rdf), format=mimetype)
    stats = {}
    ig = to_isomorphic(graph)
    result = ig.graph_digest(stats)
    print(stats)
    return result


def negative_graph_match_test():
    """Test of FRIR identifiers against tricky RDF graphs with blank nodes."""
    testInputs = [  # noqa: N806
        [
            """@prefix : <http://example.org/ns#> .
     <http://example.org> :rel
         [ :label "Same" ].
         """,
            """@prefix : <http://example.org/ns#> .
     <http://example.org> :rel
         [ :label "Same" ],
         [ :label "Same" ].
         """,
            False,
        ],
        [
            """@prefix : <http://example.org/ns#> .
     <http://example.org> :rel
         <http://example.org/a>.
         """,
            """@prefix : <http://example.org/ns#> .
     <http://example.org> :rel
         <http://example.org/a>,
         <http://example.org/a>.
         """,
            True,
        ],
        [
            """@prefix : <http://example.org/ns#> .
     :linear_two_step_symmetry_start :related [ :related [ :related :linear_two_step_symmatry_end]],
                                              [ :related [ :related :linear_two_step_symmatry_end]].""",
            """@prefix : <http://example.org/ns#> .
     :linear_two_step_symmetry_start :related [ :related [ :related :linear_two_step_symmatry_end]],
                                              [ :related [ :related :linear_two_step_symmatry_end]].""",
            True,
        ],
        [
            """@prefix : <http://example.org/ns#> .
     _:a :rel [
         :rel [
         :rel [
         :rel [
           :rel _:a;
          ];
          ];
          ];
          ].""",
            """@prefix : <http://example.org/ns#> .
     _:a :rel [
         :rel [
         :rel [
         :rel [
         :rel [
           :rel _:a;
          ];
          ];
          ];
          ];
          ].""",
            False,
        ],
        # This test fails because the algorithm purposefully breaks the symmetry of symetric
        [
            """@prefix : <http://example.org/ns#> .
     _:a :rel [
         :rel [
         :rel [
         :rel [
           :rel _:a;
          ];
          ];
          ];
          ].""",
            """@prefix : <http://example.org/ns#> .
     _:a :rel [
         :rel [
         :rel [
         :rel [
           :rel _:a;
          ];
          ];
          ];
          ].""",
            True,
        ],
        [
            """@prefix : <http://example.org/ns#> .
     _:a :rel [
         :rel [
         :label "foo";
         :rel [
         :rel [
           :rel _:a;
          ];
          ];
          ];
          ].""",
            """@prefix : <http://example.org/ns#> .
     _:a :rel [
         :rel [
         :rel [
         :rel [
           :rel _:a;
          ];
          ];
          ];
          ].""",
            False,
        ],
        [
            """@prefix : <http://example.org/ns#> .
     _:0001 :rel _:0003, _:0004.
     _:0002 :rel _:0005, _:0006.
     _:0003 :rel _:0001, _:0007, _:0010.
     _:0004 :rel _:0001, _:0009, _:0008.
     _:0005 :rel _:0002, _:0007, _:0009.
     _:0006 :rel _:0002, _:0008, _:0010.
     _:0007 :rel _:0003, _:0005, _:0009.
     _:0008 :rel _:0004, _:0006, _:0010.
     _:0009 :rel _:0004, _:0005, _:0007.
     _:0010 :rel _:0003, _:0006, _:0008.
     """,
            """@prefix : <http://example.org/ns#> .
     _:0001 :rel _:0003, _:0004.
     _:0002 :rel _:0005, _:0006.
     _:0003 :rel _:0001, _:0007, _:0010.
     _:0008 :rel _:0004, _:0006, _:0010.
     _:0009 :rel _:0004, _:0005, _:0007.
     _:0010 :rel _:0003, _:0006, _:0008.
     _:0004 :rel _:0001, _:0009, _:0008.
     _:0005 :rel _:0002, _:0007, _:0009.
     _:0006 :rel _:0002, _:0008, _:0010.
     _:0007 :rel _:0003, _:0005, _:0009.
     """,
            True,
        ],
    ]

    def fn(rdf1, rdf2, identical):
        digest1 = get_digest_value(rdf1, "text/turtle")
        digest2 = get_digest_value(rdf2, "text/turtle")
        print(rdf1)
        print(digest1)
        print(rdf2)
        print(digest2)
        assert (digest1 == digest2) == identical

    for inputs in testInputs:
        yield fn, inputs[0], inputs[1], inputs[2]


@pytest.mark.parametrize("fn, rdf1, rdf2, identical", list(negative_graph_match_test()))
def test_negative_graph_match(fn, rdf1, rdf2, identical):
    fn(rdf1, rdf2, identical)


def test_issue494_collapsing_bnodes():
    """Test for https://github.com/RDFLib/rdflib/issues/494 collapsing BNodes"""
    g = Graph()
    g += [
        (BNode("Na1a8fbcf755f41c1b5728f326be50994"), RDF["object"], URIRef("source")),
        (BNode("Na1a8fbcf755f41c1b5728f326be50994"), RDF["predicate"], BNode("vcb3")),
        (BNode("Na1a8fbcf755f41c1b5728f326be50994"), RDF["subject"], BNode("vcb2")),
        (BNode("Na1a8fbcf755f41c1b5728f326be50994"), RDF["type"], RDF["Statement"]),
        (BNode("Na713b02f320d409c806ff0190db324f4"), RDF["object"], URIRef("target")),
        (BNode("Na713b02f320d409c806ff0190db324f4"), RDF["predicate"], BNode("vcb0")),
        (BNode("Na713b02f320d409c806ff0190db324f4"), RDF["subject"], URIRef("source")),
        (BNode("Na713b02f320d409c806ff0190db324f4"), RDF["type"], RDF["Statement"]),
        (BNode("Ndb804ba690a64b3dbb9063c68d5e3550"), RDF["object"], BNode("vr0KcS4")),
        (
            BNode("Ndb804ba690a64b3dbb9063c68d5e3550"),
            RDF["predicate"],
            BNode("vrby3JV"),
        ),
        (BNode("Ndb804ba690a64b3dbb9063c68d5e3550"), RDF["subject"], URIRef("source")),
        (BNode("Ndb804ba690a64b3dbb9063c68d5e3550"), RDF["type"], RDF["Statement"]),
        (BNode("Ndfc47fb1cd2d4382bcb8d5eb7835a636"), RDF["object"], URIRef("source")),
        (BNode("Ndfc47fb1cd2d4382bcb8d5eb7835a636"), RDF["predicate"], BNode("vcb5")),
        (BNode("Ndfc47fb1cd2d4382bcb8d5eb7835a636"), RDF["subject"], URIRef("target")),
        (BNode("Ndfc47fb1cd2d4382bcb8d5eb7835a636"), RDF["type"], RDF["Statement"]),
        (BNode("Nec6864ef180843838aa9805bac835c98"), RDF["object"], URIRef("source")),
        (BNode("Nec6864ef180843838aa9805bac835c98"), RDF["predicate"], BNode("vcb4")),
        (BNode("Nec6864ef180843838aa9805bac835c98"), RDF["subject"], URIRef("source")),
        (BNode("Nec6864ef180843838aa9805bac835c98"), RDF["type"], RDF["Statement"]),
    ]

    # print('graph length: %d, nodes: %d' % (len(g), len(g.all_nodes())))
    # print('triple_bnode degrees:')
    # for triple_bnode in g.subjects(RDF['type'], RDF['Statement']):
    #     print(len(list(g.triples([triple_bnode, None, None]))))
    # print('all node degrees:')
    g_node_degs = sorted(
        [len(list(g.triples([node, None, None]))) for node in g.all_nodes()],
        reverse=True,
    )
    # print(g_node_degs)

    cg = to_canonical_graph(g)
    # print('graph length: %d, nodes: %d' % (len(cg), len(cg.all_nodes())))
    # print('triple_bnode degrees:')
    # for triple_bnode in cg.subjects(RDF['type'], RDF['Statement']):
    #     print(len(list(cg.triples([triple_bnode, None, None]))))
    # print('all node degrees:')
    cg_node_degs = sorted(
        [len(list(cg.triples([node, None, None]))) for node in cg.all_nodes()],
        reverse=True,
    )
    # print(cg_node_degs)

    assert len(g) == len(cg), "canonicalization changed number of triples in graph"
    assert len(g.all_nodes()) == len(cg.all_nodes()), (
        "canonicalization changed number of nodes in graph"
    )
    assert len(list(g.subjects(RDF["type"], RDF["Statement"]))) == len(
        list(cg.subjects(RDF["type"], RDF["Statement"]))
    ), "canonicalization changed number of statements"
    assert g_node_degs == cg_node_degs, "canonicalization changed node degrees"

    # counter for subject, predicate and object nodes
    g_pos_counts = Counter(), Counter(), Counter()
    for t in g:
        for i, node in enumerate(t):
            g_pos_counts[i][t] += 1
    g_count_signature = [sorted(c.values()) for c in g_pos_counts]

    cg = to_canonical_graph(g)
    cg_pos_counts = Counter(), Counter(), Counter()
    for t in cg:
        for i, node in enumerate(t):
            cg_pos_counts[i][t] += 1
    cg_count_signature = [sorted(c.values()) for c in cg_pos_counts]

    assert g_count_signature == cg_count_signature, (
        "canonicalization changed node position counts"
    )


def test_issue682_signing_named_graphs():
    ns = Namespace("http://love.com#")

    mary = BNode()
    john = URIRef("http://love.com/lovers/john#")

    cmary = URIRef("http://love.com/lovers/mary#")
    cjohn = URIRef("http://love.com/lovers/john#")

    store = Memory()

    g = ConjunctiveGraph(store=store)
    g.bind("love", ns)

    gmary = Graph(store=store, identifier=cmary)

    gmary.add((mary, ns["hasName"], Literal("Mary")))
    gmary.add((mary, ns["loves"], john))

    gjohn = Graph(store=store, identifier=cjohn)
    gjohn.add((john, ns["hasName"], Literal("John")))

    ig = to_isomorphic(g)
    igmary = to_isomorphic(gmary)

    assert len(igmary) == len(gmary)
    assert len(ig) == len(g)
    assert len(igmary) < len(ig)
    assert ig.graph_digest() != igmary.graph_digest()


def test_issue725_collapsing_bnodes_2():
    g = Graph()
    g += [
        (
            BNode("N0a76d42406b84fe4b8029d0a7fa04244"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#object"),
            BNode("v2"),
        ),
        (
            BNode("N0a76d42406b84fe4b8029d0a7fa04244"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate"),
            BNode("v0"),
        ),
        (
            BNode("N0a76d42406b84fe4b8029d0a7fa04244"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#subject"),
            URIRef("urn:gp_learner:fixed_var:target"),
        ),
        (
            BNode("N0a76d42406b84fe4b8029d0a7fa04244"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#Statement"),
        ),
        (
            BNode("N2f62af5936b94a8eb4b1e4bfa8e11d95"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#object"),
            BNode("v1"),
        ),
        (
            BNode("N2f62af5936b94a8eb4b1e4bfa8e11d95"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate"),
            BNode("v0"),
        ),
        (
            BNode("N2f62af5936b94a8eb4b1e4bfa8e11d95"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#subject"),
            URIRef("urn:gp_learner:fixed_var:target"),
        ),
        (
            BNode("N2f62af5936b94a8eb4b1e4bfa8e11d95"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#Statement"),
        ),
        (
            BNode("N5ae541f93e1d4e5880450b1bdceb6404"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#object"),
            BNode("v5"),
        ),
        (
            BNode("N5ae541f93e1d4e5880450b1bdceb6404"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate"),
            BNode("v4"),
        ),
        (
            BNode("N5ae541f93e1d4e5880450b1bdceb6404"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#subject"),
            URIRef("urn:gp_learner:fixed_var:target"),
        ),
        (
            BNode("N5ae541f93e1d4e5880450b1bdceb6404"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#Statement"),
        ),
        (
            BNode("N86ac7ca781f546ae939b8963895f672e"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#object"),
            URIRef("urn:gp_learner:fixed_var:source"),
        ),
        (
            BNode("N86ac7ca781f546ae939b8963895f672e"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate"),
            BNode("v0"),
        ),
        (
            BNode("N86ac7ca781f546ae939b8963895f672e"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#subject"),
            URIRef("urn:gp_learner:fixed_var:target"),
        ),
        (
            BNode("N86ac7ca781f546ae939b8963895f672e"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#Statement"),
        ),
        (
            BNode("Nac82b883ca3849b5ab6820b7ac15e490"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#object"),
            BNode("v1"),
        ),
        (
            BNode("Nac82b883ca3849b5ab6820b7ac15e490"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate"),
            BNode("v3"),
        ),
        (
            BNode("Nac82b883ca3849b5ab6820b7ac15e490"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#subject"),
            URIRef("urn:gp_learner:fixed_var:target"),
        ),
        (
            BNode("Nac82b883ca3849b5ab6820b7ac15e490"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#Statement"),
        ),
    ]

    turtle = """
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix xml: <http://www.w3.org/XML/1998/namespace> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    [] a rdf:Statement ;
        rdf:object [ ] ;
        rdf:predicate _:v0 ;
        rdf:subject <urn:gp_learner:fixed_var:target> .

    [] a rdf:Statement ;
        rdf:object _:v1 ;
        rdf:predicate _:v0 ;
        rdf:subject <urn:gp_learner:fixed_var:target> .

    [] a rdf:Statement ;
        rdf:object [ ] ;
        rdf:predicate [ ] ;
        rdf:subject <urn:gp_learner:fixed_var:target> .

    [] a rdf:Statement ;
        rdf:object <urn:gp_learner:fixed_var:source> ;
        rdf:predicate _:v0 ;
        rdf:subject <urn:gp_learner:fixed_var:target> .

    [] a rdf:Statement ;
        rdf:object _:v1 ;
        rdf:predicate [ ] ;
        rdf:subject <urn:gp_learner:fixed_var:target> ."""  # noqa: F841

    # g = Graph()
    # g.parse(data=turtle, format='turtle')

    stats = {}
    cg = rdflib.compare.to_canonical_graph(g, stats=stats)

    # print ('graph g length: %d, nodes: %d' % (len(g), len(g.all_nodes())))
    # print ('triple_bnode degrees:')
    # for triple_bnode in g.subjects(rdflib.RDF['type'], rdflib.RDF['Statement']):
    #     print (len(list(g.triples([triple_bnode, None, None]))))
    # print ('all node out-degrees:')
    # print (sorted(
    #     [len(list(g.triples([node, None, None]))) for node in g.all_nodes()]))
    # print ('all node in-degrees:')
    # print (sorted(
    #     [len(list(g.triples([None, None, node]))) for node in g.all_nodes()]))
    # print(g.serialize(format='n3'))
    #
    # print ('graph cg length: %d, nodes: %d' % (len(cg), len(cg.all_nodes())))
    # print ('triple_bnode degrees:')
    # for triple_bnode in cg.subjects(rdflib.RDF['type'],
    #                                 rdflib.RDF['Statement']):
    #     print (len(list(cg.triples([triple_bnode, None, None]))))
    # print ('all node out-degrees:')
    # print (sorted(
    #     [len(list(cg.triples([node, None, None]))) for node in cg.all_nodes()]))
    # print ('all node in-degrees:')
    # print (sorted(
    #     [len(list(cg.triples([None, None, node]))) for node in cg.all_nodes()]))
    # print(cg.serialize(format='n3'))

    assert len(g.all_nodes()) == len(cg.all_nodes())

    cg = to_canonical_graph(g)
    assert len(g) == len(cg), "canonicalization changed number of triples in graph"
    assert len(g.all_nodes()) == len(cg.all_nodes()), (
        "canonicalization changed number of nodes in graph"
    )
    assert len(list(g.subjects(RDF["type"], RDF["Statement"]))) == len(
        list(cg.subjects(RDF["type"], RDF["Statement"]))
    ), "canonicalization changed number of statements"

    # counter for subject, predicate and object nodes
    g_pos_counts = Counter(), Counter(), Counter()
    for t in g:
        for i, node in enumerate(t):
            g_pos_counts[i][t] += 1
    g_count_signature = [sorted(c.values()) for c in g_pos_counts]

    cg_pos_counts = Counter(), Counter(), Counter()
    for t in cg:
        for i, node in enumerate(t):
            cg_pos_counts[i][t] += 1
    cg_count_signature = [sorted(c.values()) for c in cg_pos_counts]

    assert g_count_signature == cg_count_signature, (
        "canonicalization changed node position counts"
    )


_TripleSet = set["_TripleType"]


class TestConsistency:
    @pytest.mark.xfail
    def test_consistent_ids(self) -> None:
        """
        This test verifies that `to_canonical_graph` creates consistent
        identifiers for blank nodes even when the graph changes.

        It does this by creating two triple sets `g0_ts` and `g1_ts`
        and then first creating a canonical graph with only the first
        triple set (cg0), and then a canonical graph with both triple
        sets (cg1), and then confirming the triples in cg0 is a subset
        of cg1.

        This will fail if the `to_canonical_graph` does not generate
        consistent identifiers for blank nodes when the graph changes.

        This property is essential for `to_canonical_graph` to
        be useful for diffing graphs.
        """
        bnode = BNode()
        g0_ts: _TripleSet = {
            (bnode, FOAF.name, Literal("Golan Trevize")),
            (bnode, RDF.type, FOAF.Person),
        }
        bnode = BNode()
        g1_ts: _TripleSet = {
            (bnode, FOAF.name, Literal("Janov Pelorat")),
            (bnode, RDF.type, FOAF.Person),
        }

        g0 = Graph()
        g0 += g0_ts
        cg0 = to_canonical_graph(g0)
        cg0_ts = GraphHelper.triple_set(cg0)

        g1 = Graph()
        g1 += g1_ts
        cg1 = to_canonical_graph(g1)
        cg1_ts = GraphHelper.triple_set(cg1)

        assert cg0_ts.issubset(cg1_ts), (
            "canonical triple set cg0_ts should be a subset of canonical triple set cg1_ts"
        )


EX = Namespace("http://example.org/")


def dataset_with_quads(*quads) -> Dataset:
    dataset = Dataset()
    for s, p, o, graph_name in quads:
        if graph_name == DATASET_DEFAULT_GRAPH_ID:
            dataset.add((s, p, o))
        else:
            dataset.add((s, p, o, dataset.graph(graph_name)))
    return dataset


class TestDatasetIsomorphic:
    def test_relabeled_bnodes(self):
        """Blank node labels, of graph names and triple terms alike, do not
        affect dataset isomorphism."""
        lhs = dataset_with_quads(
            (BNode("x"), EX.p, Literal("o"), BNode("g1")),
            (EX.d, EX.p, Literal("d"), DATASET_DEFAULT_GRAPH_ID),
        )
        rhs = dataset_with_quads(
            (BNode("y"), EX.p, Literal("o"), BNode("g2")),
            (EX.d, EX.p, Literal("d"), DATASET_DEFAULT_GRAPH_ID),
        )
        assert isomorphic(lhs, rhs)

    def test_default_graph_distinguished_from_named_graph(self):
        """The same triple in the default graph and in a named graph makes
        datasets non-isomorphic."""
        named = dataset_with_quads((EX.s, EX.p, Literal("o"), EX.g))
        bnode_named = dataset_with_quads((EX.s, EX.p, Literal("o"), BNode("g")))
        for rhs in (named, bnode_named):
            default = dataset_with_quads(
                (EX.s, EX.p, Literal("o"), DATASET_DEFAULT_GRAPH_ID)
            )
            assert not isomorphic(default, rhs)

    def test_iri_graph_name_distinguished_from_bnode_graph_name(self):
        lhs = dataset_with_quads((EX.s, EX.p, Literal("o"), EX.g))
        rhs = dataset_with_quads((EX.s, EX.p, Literal("o"), BNode("g")))
        assert not isomorphic(lhs, rhs)

    def test_different_graph_name_iris(self):
        lhs = dataset_with_quads((EX.s, EX.p, Literal("o"), EX.g1))
        rhs = dataset_with_quads((EX.s, EX.p, Literal("o"), EX.g2))
        assert not isomorphic(lhs, rhs)

    def test_graph_name_bnode_shares_scope_with_triple_bnodes(self):
        """A blank node used as graph name is the same node as the identical
        blank node inside the graph's triples."""
        lhs = dataset_with_quads((BNode("n"), EX.p, Literal("o"), BNode("n")))
        rhs = dataset_with_quads((BNode("m"), EX.p, Literal("o"), BNode("m")))
        assert isomorphic(lhs, rhs)

        distinct = dataset_with_quads((BNode("n"), EX.p, Literal("o"), BNode("g")))
        assert not isomorphic(lhs, distinct)

    def test_bnode_graphs_not_merged(self):
        """Two blank-node-named graphs are not the same as one graph with the
        combined triples."""
        split = dataset_with_quads(
            (EX.s, EX.p, Literal("o1"), BNode("g1")),
            (EX.s, EX.p, Literal("o2"), BNode("g2")),
        )
        merged = dataset_with_quads(
            (EX.s, EX.p, Literal("o1"), BNode("g1")),
            (EX.s, EX.p, Literal("o2"), BNode("g1")),
        )
        assert not isomorphic(split, merged)

    def test_empty_datasets(self):
        assert isomorphic(Dataset(), Dataset())

    def test_jsonld_roundtrip(self):
        """A Dataset serialized to JSON-LD and parsed back is isomorphic to
        the original."""
        dataset = dataset_with_quads(
            (BNode("s"), EX.p, BNode("o"), BNode("g")),
            (EX.d, EX.p, Literal("d"), DATASET_DEFAULT_GRAPH_ID),
            (EX.s, EX.p, Literal("ng"), EX.named),
        )
        roundtrip = Dataset()
        roundtrip.parse(data=dataset.serialize(format="json-ld"), format="json-ld")
        assert isomorphic(dataset, roundtrip)
