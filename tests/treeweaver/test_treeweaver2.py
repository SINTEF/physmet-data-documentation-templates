"""Tests for treeweaver2.py - the updated treeweaver implementation."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from tabular import Table, Tables
from treeweaver.treeweaver2 import (
    Entity,
    Pattern,
    Treeweaver,
    substitute,
    totable,
)

datadir = Path(__file__).resolve().parent / "data"
outdir = datadir / "output"
outdir.mkdir(parents=True, exist_ok=True)


def test_entity_substitute():
    """Test Entity.substitute() performs template substitution correctly."""
    entity = Entity(
        "sample",
        {
            "id": "sample-{sampleId}",
            "title": "{sampleId}",
            "comment": "",
        },
    )
    env = {"sampleId": "ARP001"}
    result = entity.substitute(env)

    assert result["id"] == "sample-ARP001"
    assert result["title"] == "ARP001"
    assert "comment" not in result  # Empty templates are excluded


def test_entity_substitute_raises_on_missing_variable():
    """Test Entity.substitute() raises KeyError for missing template variables."""
    entity = Entity("sample", {"id": "sample-{missing}"})
    env = {"sampleId": "ARP001"}

    with pytest.raises(KeyError):
        entity.substitute(env)


def test_pattern_document_matches_path():
    """Test Pattern.document() matches paths and returns documentation."""
    pattern = Pattern(
        "Armel/characterizations/GDmass/{sampleId}",
        {"sample": {"id": "{sampleId}", "type": "sample"}},
        {},
    )
    env = {"rootdir": "."}
    result = pattern.document("Armel/characterizations/GDmass/ARP001", env)

    assert "sample" in result
    assert result["sample"]["id"] == "ARP001"
    assert result["sample"]["type"] == "sample"


def test_pattern_document_returns_empty_for_non_matching_path():
    """Test Pattern.document() returns empty dict for non-matching paths."""
    pattern = Pattern(
        "Armel/characterizations/GDmass/{sampleId}",
        {"sample": {"id": "{sampleId}"}},
        {},
    )
    env = {"rootdir": "."}
    result = pattern.document("Other/path/ARP001", env)

    assert result == {}


def test_pattern_document_sets_file_metadata():
    """Test Pattern.document() populates file metadata (fullpath, filename, etc)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        testfile = tmppath / "test.txt"
        testfile.write_text("test")

        pattern = Pattern(
            "{name}.txt",
            {"file": {"filename": "{filename}"}},
            {},
        )
        env = {"rootdir": str(tmppath)}
        result = pattern.document("test.txt", env)

        assert result["file"]["filename"] == "test.txt"


def test_treeweaver_init_loads_config():
    """Test Treeweaver.__init__() loads configuration from YAML file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        configfile = tmppath / "config.yaml"
        configfile.write_text("""
environment:
  prefix: "arp"
entities:
  sample:
    id: "{sampleId}"
patterns:
  - "Armel/{sampleId}":
      sample:
        id: "{sampleId}"
""")

        tw = Treeweaver(configfile, rootdir=tmppath)

        assert tw.env["prefix"] == "arp"
        assert "sample" in tw.entities
        assert len(tw.patterns) > 0


def test_treeweaver_parse_conf_updates_entities():
    """Test Treeweaver.parse_conf() correctly parses and updates entities."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        configfile = tmppath / "config.yaml"
        configfile.write_text("""
environment:
  prefix: "test"
entities:
  sample:
    title: "{sampleId}"
    type: "Sample"
patterns: []
""")

        tw = Treeweaver(configfile, rootdir=tmppath)

        assert "sample" in tw.entities
        assert tw.entities["sample"]["title"] == "{sampleId}"


def test_treeweaver_document_path_single_pattern():
    """Test Treeweaver.document_path() documents a single path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        configfile = tmppath / "config.yaml"
        configfile.write_text("""
environment:
  rootdir: {}
entities:
  sample:
    id: "{{sampleId}}"
patterns:
  - "{{sampleId}}":
      sample:
        id: "{{sampleId}}"
""".format(tmppath))

        tw = Treeweaver(configfile, rootdir=tmppath)
        result = tw.document_path("ARP001")

        assert "sample" in result
        assert isinstance(result["sample"], list)


def test_treeweaver_document_recursively_traverses_tree():
    """Test Treeweaver.document() recursively traverses directory tree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "sample1").mkdir()
        (tmppath / "sample2").mkdir()

        configfile = tmppath / "config.yaml"
        configfile.write_text("""
environment:
  rootdir: {}
entities:
  dir:
    name: "{{dir_name}}"
patterns:
  - "{{dir_name}}":
      dir:
        name: "{{dir_name}}"
""".format(tmppath))

        tw = Treeweaver(configfile, rootdir=tmppath)
        result = tw.document(tmppath)

        assert "dir" in result
        assert len(result["dir"]) >= 2


def test_treeweaver_totables_converts_to_tables():
    """Test Treeweaver.totables() converts documents to Tables object."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "ARP001").mkdir()

        configfile = tmppath / "config.yaml"
        configfile.write_text("""
entities:
  sample:
    id: "{{sampleId}}"
patterns:
  - "{{sampleId}}":
      sample:
        id: "{{sampleId}}"
""".format(tmppath))

        tw = Treeweaver(configfile, rootdir=tmppath)
        tables = tw.totables(tmppath)

        assert isinstance(tables, Tables)
        assert len(tables.tables) > 0


def test_treeweaver_savedoc_writes_file():
    """Test Treeweaver.savedoc() writes documentation to file."""
    testdir = outdir / "test_treeweaver_savedoc_writes_file"
    rootdir = testdir / "Characterisation"
    (rootdir / "ARP001").mkdir(parents=True, exist_ok=True)
    configfile = testdir / "config.yaml"
    configfile.write_text("""
entities:
  sample:
    "@id": "{sampleId}"
    "@type": chameo:Sample
patterns:
  - "{sampleId}":
      sample:
        "@id": "{sampleId}"
""")

    tw = Treeweaver(configfile, rootdir=rootdir)

    # Very confusing output file name. Should be fixed in Tables.write()
    outfile = testdir / "x_sample.csv"
    tw.savedoc(rootdir, testdir / "x.csv", fmt="csv")

    assert outfile.exists()
    lines = outfile.read_text().split(os.linesep)
    assert lines[0] == "@id,@type"
    assert lines[1] == "ARP001,chameo:Sample"


def test_totable_converts_dicts_to_table():
    """Test totable() converts list of dicts to Table object."""
    dicts = [
        {"id": "ARP001", "type": "sample", "title": "Sample 1"},
        {"id": "ARP002", "type": "sample", "title": "Sample 2"},
    ]
    table = totable(dicts, name="samples")

    assert isinstance(table, Table)
    assert table.name == "samples"
    assert len(table.headers) == 3
    assert "id" in table.headers
    assert len(table.rows) == 2


def test_totable_handles_missing_keys():
    """Test totable() handles dicts with missing keys (fills with None)."""
    dicts = [
        {"id": "ARP001", "type": "sample"},
        {"id": "ARP002", "title": "Sample 2"},
    ]
    table = totable(dicts)

    assert len(table.headers) == 3
    assert len(table.rows) == 2
    # Check that missing values are represented as None
    assert None in table.rows[0]  # First row missing "title"
    assert None in table.rows[1]  # Second row missing "type"


def test_totable_preserves_column_ordering():
    """Test totable() preserves the order of headers as encountered."""
    dicts = [
        {"z": 1, "a": 2, "m": 3},
        {"z": 4, "a": 5, "m": 6},
    ]
    table = totable(dicts)

    # Headers should be in the order they were first encountered
    assert table.headers == ["z", "a", "m"]


def test_totable_handles_iterator_input():
    """Test totable() handles iterator input (converts to list)."""

    def dict_generator():
        yield {"id": "ARP001"}
        yield {"id": "ARP002"}

    table = totable(dict_generator())

    assert len(table.rows) == 2


def test_substitute_returns_primitives_unchanged():
    """Test substitute() returns primitive types unchanged."""
    assert substitute(True, {}) is True
    assert substitute(42, {}) == 42
    assert substitute(3.14, {}) == 3.14
    assert substitute(None, {}) is None


def test_substitute_processes_strings_with_format():
    """Test substitute() processes strings with .format()."""
    result = substitute("value-{key}", {"key": "123"})
    assert result == "value-123"


def test_substitute_handles_empty_strings():
    """Test substitute() returns None for empty strings."""
    result = substitute("", {})
    assert result is None


def test_substitute_processes_lists():
    """Test substitute() recursively processes lists."""
    result = substitute(["{a}", "{b}", ""], {"a": "x", "b": "y"})
    assert result == ["x", "y"]  # Empty string filtered out


def test_substitute_processes_dicts():
    """Test substitute() recursively processes nested dicts."""
    template = {
        "id": "{id}",
        "nested": {"name": "{name}"},
    }
    result = substitute(template, {"id": "123", "name": "test"})

    assert result["id"] == "123"
    assert result["nested"]["name"] == "test"


def test_treeweaver():
    """Test treeweaver class."""
    t = Treeweaver(datadir / "Armel.yaml")
    # docs = t.document("Armel/characterizations/GDmass/ARP001")
    docs = t.document(datadir)
    assert docs

    t.savedoc(datadir, outdir / "Armel.xlsx")
