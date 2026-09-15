"""Test treeweaver2"""

from pathlib import Path

from treeweaver.treeweaver2 import Treeweaver

datadir = Path(__file__).resolve().parent / "data"


def test_treeweaver() -> None:
    """Test treeweaver class."""
    t = Treeweaver(datadir / "Armel.yaml")
    doc = t.document("Armel/characterizations/GDmass/ARP001")
    assert doc
