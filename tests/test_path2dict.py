import json
import subprocess


def run_path2dict(*args):
    return subprocess.run(
        ["python", "scripts/path2dict.py", "tests/data", *args],
        capture_output=True,
        text=True,
    )


def test_path2dict_cli():
    result = run_path2dict(
        "--config",
        "/sample/instrument/method/experiment",
    )

    assert result.returncode == 0
    assert "JO11" in result.stdout
    assert (
        'sample="JM12" / instrument="SEM" / method="EDS" / '
        'experiment="220304f" /'
    ) in result.stdout


def test_path2dict_template_mints_configured_predicates():
    result = run_path2dict(
        "--config",
        "/processedFrom/isOutputOf/@id",
        "--template",
        "processedFrom=physmet:sample/{value}",
        "--template",
        "isOutputOf=physmet:instrument/{value}",
        "--json",
        "--store_path",
        "None",
    )

    assert result.returncode == 0

    rows = json.loads(result.stdout)
    assert {
        "processedFrom": "physmet:sample/JM11",
        "isOutputOf": "physmet:instrument/SEM",
        "@id": "EDS",
    } in rows


def test_path2dict_template_can_mint_at_id():
    result = run_path2dict(
        "--config",
        "/processedFrom/test/@id",
        "--template",
        "processedFrom=physmet:sample/{value}",
        "--template",
        "@id=physmet:{value}",
        "--json",
        "--store_path",
        "None",
    )

    assert result.returncode == 0

    rows = json.loads(result.stdout)
    assert {
        "processedFrom": "physmet:sample/JM11",
        "test": "SEM",
        "@id": "physmet:EDS",
    } in rows


def test_path2dict_template_rejects_conflicting_duplicates():
    result = run_path2dict(
        "--config",
        "/processedFrom/isOutputOf/@id",
        "--template",
        "processedFrom=physmet:sample/{value}",
        "--template",
        "processedFrom=physmet:other/{value}",
    )

    assert result.returncode != 0
    assert "conflicting --template definitions" in result.stderr
