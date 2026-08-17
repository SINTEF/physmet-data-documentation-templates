"""Test parse_compositions."""

from pathlib import Path

import pytest

from parse_compositions import (
    _asfloat,
    from_wtpercent,
    normalize_unit,
    parse,
    to_wtpercent,
)

# Data directory for this test module
DATADIR = Path(__file__).parent / "data" / "parse_compositions"


def test_normalize_unit():
    """Test normalize_unit()."""
    assert normalize_unit("wt%") == "wt%"
    assert normalize_unit("weight%") == "wt%"
    assert normalize_unit("mass%") == "wt%"
    assert normalize_unit("weight-percent") == "wt%"
    assert normalize_unit("at%") == "at%"
    assert normalize_unit("wt-fraction") == "wtfrac"
    assert normalize_unit("at-fraction") == "atfrac"
    with pytest.raises(ValueError):
        normalize_unit("m")


def test__asfloat():
    """Test _asfloat()."""
    assert _asfloat([10, 20, 30.0]) == [10, 20, 30]
    assert _asfloat([10, 20, 30.0, "bal"]) == [10, 20, 30, 40]

    with pytest.raises(ValueError):
        _asfloat([-10, 20, 30.0, "bal"])

    with pytest.raises(ValueError):
        _asfloat([10, 20, 80.0, "bal"])

    with pytest.raises(ValueError):
        _asfloat([10, 20, 30.0, "bal"], balance=1)


def test_to_wtpercent():
    """Test to_wtpercent()."""
    c1 = to_wtpercent(["bal", 0.5, 0.5], ["Al", "Mg", "Si"])
    assert [round(x, 2) for x in c1] == [99, 0.5, 0.5]
    c2 = to_wtpercent(["bal", 0.5, 0.5], ["Al", "Mg", "Si"], unit="at%")
    assert [round(x, 2) for x in c2] == [99.03, 0.45, 0.52]
    c3 = to_wtpercent(["bal", 0.005, 0.005], ["Al", "Mg", "Si"], unit="wtfrac")
    assert [round(x, 2) for x in c3] == [99, 0.5, 0.5]
    c4 = to_wtpercent(["bal", 0.005, 0.005], ["Al", "Mg", "Si"], unit="atfrac")
    assert [round(x, 2) for x in c4] == [99.03, 0.45, 0.52]


def test_from_wtpercent():
    """Test to_wtpercent()."""
    c1 = from_wtpercent(["bal", 0.5, 0.5], ["Al", "Mg", "Si"])
    assert [round(x, 2) for x in c1] == [99, 0.5, 0.5]
    c2 = from_wtpercent(["bal", 0.5, 0.5], ["Al", "Mg", "Si"], unit="at%")
    assert [round(x, 2) for x in c2] == [98.96, 0.55, 0.48]
    c3 = from_wtpercent(["bal", 0.5, 0.5], ["Al", "Mg", "Si"], unit="wtfrac")
    assert [round(x, 3) for x in c3] == [0.99, 0.005, 0.005]
    c4 = from_wtpercent(["bal", 0.5, 0.5], ["Al", "Mg", "Si"], unit="atfrac")
    assert [round(x, 4) for x in c4] == [0.9896, 0.0055, 0.0048]


def test_parse():
    """Test parse()."""
    from tripper import EMMO

    compositions = parse(DATADIR / "compositions.csv")
    assert compositions == [
        {
            "@id": "avb:JM",
            "@type": EMMO.ChemicalComposition,
            "hasSingleComponentComposition": [
                {
                    "@type": EMMO.SingleComponentComposition,
                    "hasSpeciesPart": EMMO.IronSymbol,
                    "hasQuantityPart": {
                        "@type": EMMO.MassFraction,
                        "hasMeasurementUnit": EMMO.WeightPercent,
                        "dataValue": 0.57,
                    },
                },
                {
                    "@type": EMMO.SingleComponentComposition,
                    "hasSpeciesPart": EMMO.ManganeseSymbol,
                    "hasQuantityPart": {
                        "@type": EMMO.MassFraction,
                        "hasMeasurementUnit": EMMO.WeightPercent,
                        "dataValue": 0.13,
                    },
                },
                {
                    "@type": EMMO.SingleComponentComposition,
                    "hasSpeciesPart": EMMO.CarbonSymbol,
                    "hasQuantityPart": {
                        "@type": EMMO.MassFraction,
                        "hasMeasurementUnit": EMMO.WeightPercent,
                        "dataValue": 0.24,
                    },
                },
                {
                    "@type": EMMO.SingleComponentComposition,
                    "hasSpeciesPart": EMMO.BoronSymbol,
                    "hasQuantityPart": {
                        "@type": EMMO.MassFraction,
                        "hasMeasurementUnit": EMMO.WeightPercent,
                        "dataValue": 0.06,
                    },
                },
            ],
        }
    ]
