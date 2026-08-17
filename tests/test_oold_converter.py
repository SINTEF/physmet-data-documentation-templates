import csv
import json
import logging
import pytest
import requests
import jsonschema
import tempfile
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource
from pathlib import Path

from oold_converter import (
    CONTEXT_URL,
    META_SCHEMA,
    ConversionError,
    infer_type,
    csv_to_json_schema,
    json_schema_to_csv,
    process_path,
)

tmp_path = tempfile.mkdtemp()

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
        response = requests.get(uri, timeout=10)
        response.raise_for_status()
        return Resource.from_contents(response.json())

    # Pre-fetch the main OO-LD meta schema to save time during tests. If the
    # network or the remote host isn't available, skip the dependent test(s)
    # instead of failing the whole run on an infrastructure issue.
    try:
        oold_meta = retrieve_schema(META_SCHEMA)
    except requests.exceptions.RequestException as e:
        pytest.skip(f"Could not reach the OO-LD meta-schema ({META_SCHEMA}): {e}")

    # Create the registry with the pre-fetched schema and the retriever for any nested $refs
    return Registry(retrieve=retrieve_schema).with_resource(META_SCHEMA, oold_meta)


# --- Tests for type inference ---


@pytest.mark.parametrize(
    "values, expected",
    [
        ([], ["string", "null"]),
        ([None, "", "  "], ["string", "null"]),
        (["true", "False", None], ["boolean", "null"]),
        (["1", "2", "true"], ["string", "null"]),  # mixed bool/number -> string
        (["1", None, "2.5", "-3.1e2"], ["number", "null"]),
        (["NaN", "Infinity", "-Infinity"], ["string", "null"]),
    ],
    ids=[
        "all-empty",
        "blank-and-none",
        "booleans-with-null",
        "mixed-bool-and-number",
        "numbers-with-null",
        "rejects-nan-and-inf",
    ],
)
def test_infer_type_not_mandatory(values, expected):
    """When a field isn't mandatory, its type stays a [type, 'null'] list - the
    value may legitimately be missing."""
    assert infer_type(values, mandatory=False) == expected
    assert infer_type(values) == expected  # mandatory defaults to False


@pytest.mark.parametrize(
    "values, expected",
    [
        (["true", "", "false"], ["boolean", "null"]),
        (["1", "", "2.5"], ["number", "null"]),
    ],
    ids=["boolean-with-blank-entry", "number-with-blank-entry"],
)
def test_infer_type_blank_entries_dont_affect_type(values, expected):
    """A blank/empty entry among otherwise-consistent booleans or numbers should
    not be mistaken for a third, conflicting type - it's just filtered out before
    the type check, and 'null' still ends up in the result because the field
    isn't mandatory."""
    assert infer_type(values) == expected


@pytest.mark.parametrize(
    "values, expected",
    [
        ([], "string"),
        (["true", "False"], "boolean"),
        (["1", "2.5", "-3.1e2"], "number"),
        (["1", "true"], "string"),  # mixed bool/number -> string
        (["hello", "world"], "string"),
    ],
    ids=[
        "all-empty",
        "booleans",
        "numbers",
        "mixed-bool-and-number",
        "strings",
    ],
)
def test_infer_type_mandatory(values, expected):
    """When a field is mandatory, 'null' is excluded entirely and the type is
    returned as a bare string rather than a list."""
    assert infer_type(values, mandatory=True) == expected


# --- Tests for CSV to JSON Schema ---


def test_csv_to_json_schema_content(data_dir: Path, tmp_path: Path):
    """Tests if the CSV parsing extracts only the first row for examples and hardcodes @id and @type."""
    input_csv = data_dir / "test_input.csv"
    csv_to_json_schema(input_csv, tmp_path)

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

    # The fixture CSV has an @id column, so only its first-row value should appear
    # (only the first row is ever extracted for examples)
    assert schema["properties"]["@id"]["examples"] == ["id:1"]

    # The fixture CSV has no @type column at all, so it should carry no examples key
    assert "examples" not in schema["properties"]["@type"]


def test_csv_to_json_schema_type_inference(tmp_path: Path):
    """Tests if type inference dynamically resolves numbers, booleans, and strings."""
    input_csv = tmp_path / "inference_test.csv"
    # Create a dynamic CSV with mixed types
    input_csv.write_text(
        "id,count,is_active,name\n1,42,true,Alice\n2,13,false,Bob", encoding="utf-8"
    )

    csv_to_json_schema(input_csv, tmp_path)

    with open(tmp_path / "Inference_test.schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)

    properties = schema["properties"]
    assert properties["id"]["type"] == ["number", "null"]
    assert properties["count"]["type"] == ["number", "null"]
    assert properties["is_active"]["type"] == ["boolean", "null"]
    assert properties["name"]["type"] == ["string", "null"]


def test_csv_to_json_schema_strict_number_inference(tmp_path: Path):
    """Tests if type inference strictly rejects NaN and Inf, falling back to string."""
    input_csv = tmp_path / "strict_numbers.csv"
    # Create a dynamic CSV with valid JSON numbers and invalid float representations
    input_csv.write_text(
        "valid_int,valid_float,valid_exp,invalid_nan,invalid_inf\n"
        "42,-3.14,1.2e-5,NaN,inf\n"
        "0,0.0,-2E10,nan,-Infinity",
        encoding="utf-8",
    )

    csv_to_json_schema(input_csv, tmp_path)

    with open(tmp_path / "Strict_numbers.schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)

    properties = schema["properties"]

    # Valid JSON numbers should be inferred as "number"
    assert properties["valid_int"]["type"] == ["number", "null"]
    assert properties["valid_float"]["type"] == ["number", "null"]
    assert properties["valid_exp"]["type"] == ["number", "null"]

    # NaN and Inf are invalid in JSON and must fallback to "string"
    assert properties["invalid_nan"]["type"] == ["string", "null"]
    assert properties["invalid_inf"]["type"] == ["string", "null"]


def test_csv_to_json_schema_no_rows_omits_examples(tmp_path: Path):
    """A CSV with headers but no data rows should produce properties with no 'examples' key at all,
    rather than an empty examples array."""
    input_csv = tmp_path / "headers_only.csv"
    input_csv.write_text("title,description\n", encoding="utf-8")

    csv_to_json_schema(input_csv, tmp_path)

    with open(tmp_path / "Headers_only.schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)

    for name, prop in schema["properties"].items():
        assert (
            "examples" not in prop
        ), f"'{name}' should not carry an empty examples array"


def test_csv_to_json_schema_base_url(data_dir: Path, tmp_path: Path):
    """Tests if providing a base URL correctly formats the $id as an IRI."""
    input_csv = data_dir / "test_input.csv"
    base_url = "https://raw.githubusercontent.com/schemas"

    csv_to_json_schema(input_csv, tmp_path, base_url=base_url)

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

    csv_to_json_schema(input_csv, tmp_path, properties_mapping=mapping)

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
    csv_to_json_schema(input_csv, tmp_path)

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
        csv_to_json_schema(missing_file, tmp_path)


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

    json_schema_to_csv(input_json, tmp_path)

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


def test_json_schema_to_csv_filename_without_schema_suffix(tmp_path: Path):
    """A JSON filename not ending in '.schema.json' falls back to Path.stem, and the
    output CSV name is still lowercased."""
    input_json = tmp_path / "MySchema.json"
    mock_schema = {"properties": {"name": {"examples": ["Alice"]}}}
    input_json.write_text(json.dumps(mock_schema), encoding="utf-8")

    json_schema_to_csv(input_json, tmp_path)

    assert (tmp_path / "myschema.csv").exists()


def test_json_schema_to_csv_matches_fixture_csv(data_dir: Path, tmp_path: Path):
    """Converting the paired schema fixture (2 examples per property, including a
    null) back to CSV should reproduce the original test_input.csv fixture's rows
    exactly - a genuine round trip using real files rather than an inline mock."""
    input_json = data_dir / "test_input_schema.json"
    json_schema_to_csv(input_json, tmp_path)

    # The fixture is named "test_input_schema.json" (no ".schema.json" suffix), so
    # the output filename is derived from Path.stem, lowercased.
    output_file = tmp_path / "test_input_schema.csv"
    assert output_file.exists(), "The CSV file was not created."

    with open(output_file, "r", encoding="utf-8") as f:
        actual_rows = list(csv.DictReader(f))

    with open(data_dir / "test_input.csv", "r", encoding="utf-8") as f:
        expected_rows = list(csv.DictReader(f))

    assert actual_rows == expected_rows


def test_json_schema_to_csv_invalid_schema(data_dir: Path, tmp_path: Path):
    """Tests error handling when the JSON file lacks a 'properties' key."""
    input_json = data_dir / "invalid_schema.json"

    with pytest.raises(ValueError, match="missing the 'properties' key"):
        json_schema_to_csv(input_json, tmp_path)


def test_json_schema_to_csv_file_not_found(tmp_path: Path):
    """Tests error handling for missing JSON files."""
    missing_file = tmp_path / "does_not_exist.json"
    with pytest.raises(FileNotFoundError):
        json_schema_to_csv(missing_file, tmp_path)


# --- Tests for Directory Path Processing ---


def test_process_path_directory(data_dir: Path, tmp_path: Path):
    """Tests if process_path correctly processes a folder based on mode."""
    process_path(data_dir, tmp_path, "csv2json")

    expected_output = tmp_path / "Test_input.schema.json"
    assert (
        expected_output.exists()
    ), "The directory processor failed to generate the schema."


def test_process_path_directory_skips_mismatched_files(tmp_path: Path, caplog):
    """Files in a directory that don't match the requested mode are silently skipped,
    and a summary warning is logged when nothing ends up processed."""
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "notes.txt").write_text("not convertible", encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        process_path(input_dir, tmp_path / "out", "csv2json")

    assert "No files were processed" in caplog.text


def test_process_path_single_unsupported_file_warns(tmp_path: Path, caplog):
    """A single file explicitly passed in that doesn't match the mode logs a
    file-specific warning (as opposed to the directory case, which stays quiet
    per-file and only summarizes at the end)."""
    bad_file = tmp_path / "notes.txt"
    bad_file.write_text("not convertible", encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        process_path(bad_file, tmp_path / "out", "csv2json")

    assert "unsupported for mode" in caplog.text


def test_process_path_missing_input(tmp_path: Path):
    """Tests error handling for a completely missing input path."""
    missing = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        process_path(missing, tmp_path / "out", "csv2json")


# --- Tests for ConversionError ---


if 1:
    # def test_conversion_error_wraps_original_exception():
    """ConversionError should preserve the underlying exception for callers that want it."""
    original = ValueError("boom")
    err = ConversionError("wrapped failure", original)

    assert str(err) == "wrapped failure"
    assert err.original_exception is original
