import json
import subprocess


def run_path2dict(*args, path="tests/data"):
    return subprocess.run(
        ["python", "scripts/path2dict.py", path, "--intent", "dataset", *args],
        capture_output=True,
        text=True,
    )


def write_treeweaver(path, text):
    path.joinpath("treeweaver.yaml").write_text(text, encoding="utf-8")


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


def test_path2dict_template_can_rewrite_existing_fields():
    result = run_path2dict(
        "--config",
        "/processedFrom/isOutputOf/@id",
        "--template",
        "processedFrom=physmet:sample/{processedFrom}",
        "--template",
        "isOutputOf=physmet:instrument/{isOutputOf}",
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
        "processedFrom=physmet:sample/{processedFrom}",
        "--template",
        "@id=physmet:{@id}",
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


def test_path2dict_template_can_add_derived_field():
    result = run_path2dict(
        "--config",
        "/processedFrom/test/@id",
        "--template",
        "newProp={processedFrom}_{@id}",
        "--json",
        "--store_path",
        "None",
    )

    assert result.returncode == 0

    rows = json.loads(result.stdout)
    assert {
        "processedFrom": "JM11",
        "test": "SEM",
        "@id": "EDS",
        "newProp": "JM11_EDS",
    } in rows


def test_path2dict_template_can_add_constant_field():
    result = run_path2dict(
        "--config",
        "/processedFrom/test/@id",
        "--template",
        "kind=dataset",
        "--json",
        "--store_path",
        "None",
    )

    assert result.returncode == 0

    rows = json.loads(result.stdout)
    assert {
        "processedFrom": "JM11",
        "test": "SEM",
        "@id": "EDS",
        "kind": "dataset",
    } in rows


def test_path2dict_template_rejects_conflicting_duplicates():
    result = run_path2dict(
        "--config",
        "/processedFrom/isOutputOf/@id",
        "--template",
        "processedFrom=physmet:sample/{processedFrom}",
        "--template",
        "processedFrom=physmet:other/{processedFrom}",
    )

    assert result.returncode != 0
    assert "conflicting --template definitions" in result.stderr


def test_treeweaver_root_config_is_loaded(tmp_path):
    write_treeweaver(
        tmp_path,
        """
root: true
version: 1
intents:
  dataset:
    config: "/{sample}"
""",
    )
    tmp_path.joinpath("JM11").mkdir()

    result = run_path2dict("--json", "--store_path", "None", path=str(tmp_path))

    assert result.returncode == 0
    assert {"sample": "JM11"} in json.loads(result.stdout)


def test_treeweaver_selected_intent_is_used(tmp_path):
    write_treeweaver(
        tmp_path,
        """
root: true
version: 1
intents:
  dataset:
    config: "/{dataset}"
  sample:
    config: "/{sample}"
""",
    )
    tmp_path.joinpath("DS1").mkdir()

    result = run_path2dict("--json", "--store_path", "None", path=str(tmp_path))

    assert result.returncode == 0
    assert {"dataset": "DS1"} in json.loads(result.stdout)


def test_treeweaver_unselected_intents_are_ignored(tmp_path):
    write_treeweaver(
        tmp_path,
        """
root: true
version: 1
intents:
  dataset:
    config: "/{dataset}"
  sample:
    config: "/{sample}"
    template:
      bad: "{missing}"
""",
    )
    tmp_path.joinpath("DS1").mkdir()

    result = run_path2dict("--json", "--store_path", "None", path=str(tmp_path))

    assert result.returncode == 0
    assert {"dataset": "DS1"} in json.loads(result.stdout)


def test_treeweaver_child_config_overrides_parent_config(tmp_path):
    write_treeweaver(
        tmp_path,
        """
root: true
version: 1
intents:
  dataset:
    config: "/{sample}"
""",
    )
    sample = tmp_path / "JM11"
    sample.mkdir()
    write_treeweaver(
        sample,
        """
version: 1
intents:
  dataset:
    config: "{sample}/{dataset}"
""",
    )
    sample.joinpath("EDS").mkdir()

    result = run_path2dict("--json", "--store_path", "None", path=str(tmp_path))

    assert result.returncode == 0
    assert {"sample": "JM11", "dataset": "EDS"} in json.loads(result.stdout)


def test_treeweaver_child_config_merges_template(tmp_path):
    write_treeweaver(
        tmp_path,
        """
root: true
version: 1
intents:
  dataset:
    config: "/{sample}/{dataset}"
    template:
      type: "physmet:Dataset"
""",
    )
    sample = tmp_path / "JM11"
    sample.mkdir()
    write_treeweaver(
        sample,
        """
version: 1
intents:
  dataset:
    template:
      label: "{dataset}"
""",
    )
    sample.joinpath("EDS").mkdir()

    result = run_path2dict("--json", "--store_path", "None", path=str(tmp_path))

    assert result.returncode == 0
    assert {
        "sample": "JM11",
        "dataset": "EDS",
        "type": "physmet:Dataset",
        "label": "EDS",
    } in json.loads(result.stdout)


def test_treeweaver_child_template_can_use_parent_context(tmp_path):
    write_treeweaver(
        tmp_path,
        """
root: true
version: 1
intents:
  dataset:
    config: "/{sample}/{dataset}"
    template:
      "@id": "physmet:dataset/{dataset}"
      processedFrom: "physmet:sample/{sample}"
""",
    )
    sample = tmp_path / "JM11"
    sample.mkdir()
    write_treeweaver(
        sample,
        """
version: 1
intents:
  dataset:
    config: "/{measurement}"
    template:
      label: "{processedFrom}/{@id}/{measurement}"
""",
    )
    sample.joinpath("EDS").mkdir()

    result = run_path2dict("--json", "--store_path", "None", path=str(tmp_path))

    assert result.returncode == 0
    assert {
        "sample": "JM11",
        "dataset": "EDS",
        "@id": "physmet:dataset/EDS",
        "processedFrom": "physmet:sample/JM11",
        "measurement": "EDS",
        "label": "physmet:sample/JM11/physmet:dataset/EDS/EDS",
    } in json.loads(result.stdout)


def test_treeweaver_cli_config_override_wins_over_yaml(tmp_path):
    write_treeweaver(
        tmp_path,
        """
root: true
version: 1
intents:
  dataset:
    config: "/{sample}"
""",
    )
    tmp_path.joinpath("JM11", "EDS").mkdir(parents=True)

    result = run_path2dict(
        "--config",
        "/{sample}/{dataset}",
        "--json",
        "--store_path",
        "None",
        path=str(tmp_path),
    )

    assert result.returncode == 0
    assert {"sample": "JM11", "dataset": "EDS"} in json.loads(result.stdout)


def test_treeweaver_config_file_provenance_is_retained(tmp_path):
    write_treeweaver(
        tmp_path,
        """
root: true
version: 1
intents:
  dataset:
    config: "/{sample}/{dataset}"
""",
    )
    sample = tmp_path / "JM11"
    sample.mkdir()
    write_treeweaver(
        sample,
        """
version: 1
intents:
  dataset:
    template:
      label: "{dataset}"
""",
    )
    sample.joinpath("EDS").mkdir()

    result = run_path2dict(
        "--json",
        "--store_path",
        "None",
        "--store_config_provenance",
        "configFiles",
        path=str(tmp_path),
    )

    assert result.returncode == 0
    row = json.loads(result.stdout)[0]
    assert str(tmp_path / "treeweaver.yaml") in row["configFiles"]
    assert str(sample / "treeweaver.yaml") in row["configFiles"]
