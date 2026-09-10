"""Test treeweaver metadata."""

from pathlib import Path

from treeweaver.metadata import Scope

datadir = Path(__file__).resolve().parent / "data"


def test_scope():
    """Test scope."""

    s = Scope()
    s.add("_prefix", "ex", comment="Example prefix.")

    assert "_prefix" in s
    assert "a" not in s
    assert s["_prefix"] == "ex"
    assert s.get("_prefix") == "ex"
    assert s.get("prefix1") is None
    assert s.get("_prefix", "owl") == "ex"
    assert s.get("prefix1", "owl") == "owl"

    s2 = s.copy()
    s.add("_prefix", "ex2")
    assert s["_prefix"] == "ex2"
    assert s2["_prefix"] == "ex"
    assert list(s) == ["_prefix"]  # test iteration

    # __FIXME__: should not be necessary to set sniff_dialect=False
    s3 = s.merge(datadir / "__METADATA__.csv", sniff_dialect=False)
    assert s3["_prefix"] == "arp"
    assert s3["@type"] == ["emmo:Dataset", "dcat:Dataset"]
    assert s3.getoptions("@type") == {"sep": ";", "append": True}

    doc = s3.document("data")
    assert doc["@id"] == "arp:data"
    assert doc["title"] == "data"
    assert doc["rightsHolder"] == "org:NTNU"
