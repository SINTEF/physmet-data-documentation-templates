import csv
import json
import pytest
import requests
import jsonschema
from jsonschema.exceptions import ValidationError
from pathlib import Path

from oold_converter import *

# --- Fixtures ---


@pytest.fixture
def data_dir() -> Path:
    """Returns the path to the static test data directory."""
    # This resolves to tests/data/oold_converter relative to this test file
    return Path(__file__).parent / "data" / "oold_converter"


@pytest.fixture(scope="session")
def oold_meta_schema():
    response = requests.get(META_SCHEMA)
    response.raise_for_status()
    return response.json()


# --- Tests for CSV to JSON Schema ---


def test_csv_to_json_schema_content(data_dir: Path, tmp_path: Path):
    """Tests if the CSV parsing extracts headers and examples with correct null handling."""
    input_csv = data_dir / "test_input.csv"
    csv_to_json_schema(str(input_csv), str(tmp_path))

    output_file = tmp_path / "test_input.schema.json"
    assert output_file.exists(), "The JSON schema was not created."

    with open(output_file, "r", encoding="utf-8") as f:
        schema = json.load(f)

    assert schema["$id"] == "test_input.schema.json"
    assert "properties" in schema
    assert "title" in schema["properties"]

    # Check that type is correctly allowing nulls and description is empty string
    assert schema["properties"]["title"]["type"] == ["string", "null"]
    assert schema["properties"]["title"]["description"] == ""
    assert schema["properties"]["title"]["examples"] == ["Sample 1", "Sample 2"]

    assert schema["properties"]["description"]["examples"] == ["Desc 1", None]


def test_csv_to_json_schema_oold_compliance(
    data_dir: Path, tmp_path: Path, oold_meta_schema
):
    """Strictly validates the generated JSON against the official OO-LD meta-schema."""
    input_csv = data_dir / "test_input.csv"
    csv_to_json_schema(str(input_csv), str(tmp_path))

    output_file = tmp_path / "test_input.schema.json"
    with open(output_file, "r", encoding="utf-8") as f:
        generated_schema = json.load(f)

    try:
        jsonschema.validate(instance=generated_schema, schema=oold_meta_schema)
    except ValidationError as e:
        pytest.fail(f"Schema failed OO-LD validation: {e.message}")


def test_csv_to_json_file_not_found(tmp_path: Path):
    """Tests error handling for missing CSV files."""
    missing_file = tmp_path / "does_not_exist.csv"
    with pytest.raises(FileNotFoundError):
        csv_to_json_schema(str(missing_file), str(tmp_path))


# --- Tests for JSON Schema to CSV ---


def test_json_schema_to_csv_content(data_dir: Path, tmp_path: Path):
    """Tests if the schema correctly unpacks array examples into CSV rows."""
    input_json = data_dir / "test_input.schema.json"
    json_schema_to_csv(str(input_json), str(tmp_path))

    output_file = tmp_path / "test_input.csv"
    assert output_file.exists(), "The CSV file was not created."

    with open(output_file, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    assert len(reader) == 2
    assert reader[0]["title"] == "Sample 1"
    assert reader[1]["@id"] == "id:2"
    assert reader[1]["description"] == ""


def test_json_schema_to_csv_invalid_schema(data_dir: Path, tmp_path: Path):
    """Tests error handling when the JSON file lacks a 'properties' key."""
    input_json = data_dir / "invalid_schema.json"

    with pytest.raises(ValueError, match="missing the 'properties' key"):
        json_schema_to_csv(str(input_json), str(tmp_path))


def test_json_schema_to_csv_file_not_found(tmp_path: Path):
    """Tests error handling for missing JSON files."""
    missing_file = tmp_path / "does_not_exist.json"
    with pytest.raises(FileNotFoundError):
        json_schema_to_csv(str(missing_file), str(tmp_path))


# --- Tests for Directory Path Processing ---


def test_process_path_directory(data_dir: Path, tmp_path: Path):
    """Tests if process_path correctly processes a folder based on mode."""
    # Process the entire directory in csv2json mode
    process_path(str(data_dir), str(tmp_path), "csv2json")

    # It should have found test_input.csv and generated the schema
    expected_output = tmp_path / "test_input.schema.json"
    assert (
        expected_output.exists()
    ), "The directory processor failed to generate the schema."
