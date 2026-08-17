import csv
import json
import pytest
import requests
import jsonschema
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource
from pathlib import Path

from oold_converter import *

# --- Fixtures ---


@pytest.fixture
def data_dir() -> Path:
    """Returns the path to the static test data directory."""
    return Path(__file__).parent / "data" / "oold_converter"


@pytest.fixture(scope="session")
def schema_registry():
    """
    Creates a referencing Registry that explicitly allows fetching remote schemas.
    This safely prevents the jsonschema DeprecationWarning about auto-fetching URLs.
    """

    def retrieve_schema(uri):
        response = requests.get(uri)
        response.raise_for_status()
        return Resource.from_contents(response.json())

    # Pre-fetch the main OO-LD meta schema to save time during tests
    oold_meta = retrieve_schema(META_SCHEMA)

    # Create the registry with the pre-fetched schema and the retriever for any nested $refs
    return Registry(retrieve=retrieve_schema).with_resource(META_SCHEMA, oold_meta)


# --- Tests for CSV to JSON Schema ---


def test_csv_to_json_schema_content(data_dir: Path, tmp_path: Path):
    """Tests if the CSV parsing extracts only the first row for examples and hardcodes @id and @type."""
    input_csv = data_dir / "test_input.csv"
    csv_to_json_schema(str(input_csv), str(tmp_path))

    output_file = tmp_path / "Test_input.schema.json"
    assert output_file.exists(), "The JSON schema was not created."

    with open(output_file, "r", encoding="utf-8") as f:
        schema = json.load(f)

    assert schema["$id"] == "Test_input.schema.json"
    assert schema["title"] == "Test_input"
    assert "properties" in schema
    assert "title" in schema["properties"]

    # Verify that @id and @type are unconditionally added and marked as required
    assert "@id" in schema["properties"]
    assert "@type" in schema["properties"]
    assert "required" in schema
    assert "@id" in schema["required"]
    assert "@type" in schema["required"]

    # Check that the specific anyOf pattern is hardcoded correctly
    assert "anyOf" in schema["properties"]["@type"]
    assert len(schema["properties"]["@type"]["anyOf"]) == 2

    # Verify types and examples
    assert schema["properties"]["title"]["type"] == ["string", "null"]
    assert schema["properties"]["title"]["examples"] == ["Sample 1"]
    assert schema["properties"]["description"]["examples"] == ["Desc 1"]


def test_csv_to_json_schema_type_inference(tmp_path: Path):
    """Tests if type inference dynamically resolves integers, booleans, and strings."""
    input_csv = tmp_path / "inference_test.csv"
    # Create a dynamic CSV with mixed types
    input_csv.write_text(
        "id,count,is_active,name\n1,42,true,Alice\n2,13,false,Bob", encoding="utf-8"
    )

    csv_to_json_schema(str(input_csv), str(tmp_path))

    with open(tmp_path / "Inference_test.schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)

    properties = schema["properties"]
    assert properties["id"]["type"] == ["number", "null"]
    assert properties["count"]["type"] == ["number", "null"]
    assert properties["is_active"]["type"] == ["boolean", "null"]
    assert properties["name"]["type"] == ["string", "null"]


def test_csv_to_json_schema_base_url(data_dir: Path, tmp_path: Path):
    """Tests if providing a base URL correctly formats the $id as an IRI."""
    input_csv = data_dir / "test_input.csv"
    base_url = "https://raw.githubusercontent.com/schemas"

    csv_to_json_schema(str(input_csv), str(tmp_path), base_url=base_url)

    output_file = tmp_path / "Test_input.schema.json"
    with open(output_file, "r", encoding="utf-8") as f:
        schema = json.load(f)

    assert schema["$id"] == f"{base_url}/Test_input.schema.json"


def test_csv_to_json_schema_properties_mapping(data_dir: Path, tmp_path: Path):
    """Tests if mapping ONLY extracts description/conformance and safely ignores other properties."""
    input_csv = data_dir / "test_input.csv"

    mapping = {
        "title": {
            "iri": "dcterms:title",
            "range": "rdfs:Literal",
            "conformance": "mandatory",
            "datatype": "rdf:langString",
            "usageNote": "A name given to the resource.",
            "description": "My Custom Title Description",
        }
    }

    csv_to_json_schema(str(input_csv), str(tmp_path), properties_mapping=mapping)

    output_file = tmp_path / "Test_input.schema.json"
    with open(output_file, "r", encoding="utf-8") as f:
        schema = json.load(f)

    properties = schema["properties"]

    # Conformance was 'mandatory', so it should be required and the type should drop 'null'
    assert "required" in schema
    assert "title" in schema["required"]
    assert properties["title"]["type"] == "string"

    # Description should have been successfully injected
    assert properties["title"]["description"] == "My Custom Title Description"

    # Verify that ALL other metadata values were correctly ignored
    assert "iri" not in properties["title"]
    assert "range" not in properties["title"]
    assert "conformance" not in properties["title"]
    assert "datatype" not in properties["title"]
    assert "usageNote" not in properties["title"]


def test_csv_to_json_schema_oold_compliance(
    data_dir: Path, tmp_path: Path, schema_registry
):
    """Strictly validates the generated JSON against the official OO-LD meta-schema."""
    input_csv = data_dir / "test_input.csv"
    csv_to_json_schema(str(input_csv), str(tmp_path))

    output_file = tmp_path / "Test_input.schema.json"
    with open(output_file, "r", encoding="utf-8") as f:
        generated_schema = json.load(f)

    try:
        # We retrieve the main schema from the registry and validate against it.
        # Passing the registry explicitly silences the jsonschema DeprecationWarning.
        oold_meta_schema = schema_registry.resolver().lookup(META_SCHEMA).contents
        jsonschema.validate(
            instance=generated_schema, schema=oold_meta_schema, registry=schema_registry
        )
    except ValidationError as e:
        pytest.fail(f"Schema failed OO-LD validation: {e.message}")


def test_csv_to_json_file_not_found(tmp_path: Path):
    """Tests error handling for missing CSV files."""
    missing_file = tmp_path / "does_not_exist.csv"
    with pytest.raises(FileNotFoundError):
        csv_to_json_schema(str(missing_file), str(tmp_path))


# --- Tests for JSON Schema to CSV ---


def test_json_schema_to_csv_content(tmp_path: Path):
    """Tests if the schema correctly unpacks array examples into CSV rows (expecting 1 row)."""
    # Create a dynamic mock schema with 1 example and hardcoded keys
    input_json = tmp_path / "Test_input.schema.json"
    mock_schema = {
        "$schema": META_SCHEMA,
        "$id": "Test_input.schema.json",
        "@context": CONTEXT_URL,
        "title": "Test_input",
        "type": "object",
        "properties": {
            "@id": {
                "anyOf": [{"type": "string", "format": "uri"}],
                "description": "",
                "examples": ["id:1"],
            },
            "@type": {
                "anyOf": [{"type": "string", "format": "uri"}],
                "description": "",
                "examples": ["type:1"],
            },
            "title": {
                "type": ["string", "null"],
                "description": "",
                "examples": ["Sample 1"],
            },
            "description": {
                "type": ["string", "null"],
                "description": "",
                "examples": ["Desc 1"],
            },
        },
    }
    with open(input_json, "w", encoding="utf-8") as f:
        json.dump(mock_schema, f)

    json_schema_to_csv(str(input_json), str(tmp_path))

    output_file = tmp_path / "test_input.csv"
    assert output_file.exists(), "The CSV file was not created."

    with open(output_file, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    # Expecting exactly 1 row based on the new logic
    assert len(reader) == 1
    assert reader[0]["title"] == "Sample 1"
    assert reader[0]["@id"] == "id:1"
    assert reader[0]["@type"] == "type:1"
    assert reader[0]["description"] == "Desc 1"


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
    process_path(str(data_dir), str(tmp_path), "csv2json")

    expected_output = tmp_path / "Test_input.schema.json"
    assert (
        expected_output.exists()
    ), "The directory processor failed to generate the schema."
