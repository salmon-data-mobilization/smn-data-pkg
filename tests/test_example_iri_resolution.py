"""Check the minimal example's selected terms, including their published RDF."""

from __future__ import annotations

import csv
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag
from urllib.request import Request, urlopen

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, SKOS


ROOT = Path(__file__).resolve().parents[1]
DICTIONARY = ROOT / "examples" / "minimal-example" / "metadata" / "column_dictionary.csv"

# The spawner count in this example is named NATURAL_SPAWNERS_TOTAL in the CSV.
SPAWNER_COLUMN = "NATURAL_SPAWNERS_TOTAL"
SPAWNER_ABUNDANCE = "https://w3id.org/gcdfo/salmon#SpawnerAbundance"
NATURAL_ORIGIN = "https://w3id.org/smn/NaturalOrigin"
ABUNDANCE = "https://w3id.org/smn/Abundance"
FETCH_TIMEOUT_SECONDS = 5


def spawner_row() -> dict[str, str]:
    """Select by column name so CSV row order cannot change the assertion."""
    with DICTIONARY.open(newline="", encoding="utf-8") as source:
        rows = [
            row
            for row in csv.DictReader(source)
            if row["column_name"] == SPAWNER_COLUMN
        ]
    if len(rows) != 1:
        raise AssertionError(f"expected one {SPAWNER_COLUMN} row, found {len(rows)}")
    return rows[0]


def require_rdf_type(graph: Graph, iri: str, expected_type: URIRef) -> None:
    """Require this subject's type; a document's HTTP 200 alone proves nothing."""
    if (URIRef(iri), RDF.type, expected_type) not in graph:
        raise AssertionError(f"{iri} has no rdf:type {expected_type} in its Turtle document")


def fetch_turtle(iri: str) -> Graph:
    """Dereference a term's document with Turtle negotiation and a short timeout."""
    document_iri, _ = urldefrag(iri)
    request = Request(document_iri, headers={"Accept": "text/turtle"})
    with urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
        document = response.read()
    return Graph().parse(data=document, format="turtle", publicID=document_iri)


class ExampleIriResolutionTests(unittest.TestCase):
    def test_minimal_spawner_row_uses_selected_terms(self) -> None:
        row = spawner_row()
        self.assertEqual(SPAWNER_ABUNDANCE, row["term_iri"])
        self.assertEqual("owl_class", row["term_type"])
        self.assertEqual(NATURAL_ORIGIN, row["constraint_iri"])
        self.assertEqual(ABUNDANCE, row["property_iri"])

    def test_type_check_rejects_missing_fragment_and_wrong_type_offline(self) -> None:
        graph = Graph().parse(
            data="""
                @prefix owl: <http://www.w3.org/2002/07/owl#> .
                @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
                <https://example.org/terms#Present> a owl:Class .
                <https://example.org/terms#Concept> a skos:Concept .
            """,
            format="turtle",
        )
        require_rdf_type(graph, "https://example.org/terms#Present", OWL.Class)
        with self.assertRaisesRegex(AssertionError, "#Missing has no rdf:type"):
            require_rdf_type(graph, "https://example.org/terms#Missing", OWL.Class)
        with self.assertRaisesRegex(AssertionError, "#Concept has no rdf:type"):
            require_rdf_type(graph, "https://example.org/terms#Concept", OWL.Class)

    def test_published_documents_contain_each_term_with_its_type(self) -> None:
        # The positive control checks that this runner can retrieve and parse
        # the known-good smn:Abundance document. It measures network reach and
        # Turtle delivery, not the existence of either target term. Skip only
        # on a transport outage; an HTTP response, invalid Turtle or a missing
        # triple is a failure. This skip retires when this check moves to a
        # network-required job where transport failure must fail the build.
        try:
            abundance_graph = fetch_turtle(ABUNDANCE)
        except HTTPError as error:
            self.fail(f"known-good {ABUNDANCE} returned HTTP {error.code}")
        except (URLError, TimeoutError, OSError) as error:
            raise unittest.SkipTest(f"cannot reach known-good {ABUNDANCE}: {error}") from error
        require_rdf_type(abundance_graph, ABUNDANCE, OWL.Class)

        row = spawner_row()
        for field, expected_type in (
            ("term_iri", OWL.Class),
            ("constraint_iri", SKOS.Concept),
            ("property_iri", OWL.Class),
        ):
            iri = row[field]
            with self.subTest(field=field, iri=iri):
                if iri == ABUNDANCE:
                    graph = abundance_graph
                else:
                    try:
                        graph = fetch_turtle(iri)
                    except HTTPError as error:
                        self.fail(f"{field} {iri} returned HTTP {error.code}")
                    except (URLError, TimeoutError, OSError) as error:
                        # If the positive control has also become unreachable,
                        # this is a genuine outage. If it still works, the
                        # target's failed dereference is a broken example.
                        try:
                            fetch_turtle(ABUNDANCE)
                        except HTTPError as probe_error:
                            self.fail(
                                f"known-good {ABUNDANCE} returned HTTP {probe_error.code}"
                            )
                        except (URLError, TimeoutError, OSError) as probe_error:
                            raise unittest.SkipTest(
                                f"ontology network became unreachable: {probe_error}"
                            ) from probe_error
                        self.fail(f"{field} {iri} cannot be reached while {ABUNDANCE} can: {error}")
                require_rdf_type(graph, iri, expected_type)
