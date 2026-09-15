"""Test treeweaver metadata."""

from pathlib import Path

from treeweaver.scope import Scope

datadir = Path(__file__).resolve().parent / "data"

if 1:
    # def test_scope():
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
    new = Scope.fromtable(datadir / "__METADATA__.csv", sniff_dialect=False)
    s3 = s.merged(new)
    assert s3["_prefix"] == "arp"
    assert s3["@type"] == "emmo:Dataset;dcat:Dataset"
    assert s3.getoptions("@type") == {"sep": ";", "append": True}

    doc3 = s3.document(datadir)
    assert doc3["@id"] == f"arp:data"
    assert doc3["title"] == "data"
    assert doc3["rightsHolder"] == "org:NTNU"
    assert doc3["creator"] == "pers:ArmelPerrotin"
    assert doc3["contactPoint"] == "pers:MarisaDiSabatino"
    assert doc3["distribution.downloadURL"].endswith("/Armel")

    s4 = Scope.frominfo(datadir / "info.yaml")
    assert s4["_prefix"] == "avb"

    doc4 = s4.document(datadir)
    assert doc4["@id"] == f"avb:data"
    assert doc4["title"] == "data"
    assert doc4["rightsHolder"] == "org:NTNU"
    assert doc4["distribution.downloadURL"].endswith(
        "/Andreas%20Voll%20Bugten%20data"
    )
