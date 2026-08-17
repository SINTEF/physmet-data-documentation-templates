import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure package-level logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("oold.converter")

# Global schemas and contexts
CONTEXT_URL = "https://raw.githubusercontent.com/SINTEF/physmet-data-documentation-templates/refs/heads/main/schema/context.json"
META_SCHEMA = "https://oo-ld.org/latest/meta/oold-meta-schema.json"


class ConversionError(Exception):
    """Error raised when conversion between formats fails.

    Args:
        message (str): The error description.
        original_exception (Exception, optional): The caught exception causing the error.
    """

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception


def _infer_type(values: List[Optional[str]]) -> List[str]:
    """
    Infers the JSON schema data type based on a list of string values.

    Args:
        values (List[Optional[str]]): The column values extracted from the CSV.

    Returns:
        List[str]: A list containing the inferred type and "null" (e.g., ["number", "null"]).
    """
    non_nulls = [v.strip() for v in values if v is not None and v.strip() != ""]
    if not non_nulls:
        return ["string", "null"]

    is_bool = True
    is_number = True

    for v in non_nulls:
        if v.lower() not in ["true", "false"]:
            is_bool = False
        if is_number:
            try:
                float(v)
            except ValueError:
                is_number = False

    if is_bool:
        return ["boolean", "null"]
    if is_number:
        return ["number", "null"]
    return ["string", "null"]


def csv_to_json_schema(
    input_file: str,
    output_folder: str,
    base_url: Optional[str] = None,
    properties_mapping: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Reads a CSV file and generates an OO-LD JSON Schema.

    Infers the type dynamically from the column data. Extract only `description` and
    `conformance` from the properties mapping. `@id` and `@type` are unconditionally
    hardcoded as mandatory fields. Extracts only the first row of examples from the CSV.
    The resulting schema's title, filename, and `$id` fields are capitalized.

    Args:
        input_file (str): Path to the input CSV file.
        output_folder (str): Directory where the JSON schema will be saved.
        base_url (Optional[str]): A URL to prepend to the `$id` to create a valid IRI.
        properties_mapping (Optional[Dict[str, Any]]): Dictionary mapping column headers
            to their OO-LD metadata definitions.

    Raises:
        FileNotFoundError: If the input CSV file does not exist.
        ConversionError: If parsing the CSV or writing the JSON file fails.
    """
    file_path = Path(input_file)

    if not file_path.exists() or not file_path.is_file():
        logger.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(
            f"The specified input CSV file does not exist: {input_file}"
        )

    # Capitalize the stem for the schema title and filename
    file_stem = file_path.stem.capitalize()
    schema_filename = f"{file_stem}.schema.json"

    # Construct a valid IRI for $id if base_url is provided
    if base_url:
        schema_id = f"{base_url.rstrip('/')}/{schema_filename}"
    else:
        schema_id = schema_filename

    schema: Dict[str, Any] = {
        "$schema": META_SCHEMA,
        "$id": schema_id,
        "@context": CONTEXT_URL,
        "title": file_stem,
        "type": "object",
        "properties": {},
    }

    logger.info(f"Reading CSV file: {input_file}")

    try:
        with open(input_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            rows = list(reader)
            required_fields = ["@id", "@type"]

            # Unconditionally hardcode @id and @type definitions
            schema["properties"]["@id"] = {
                "anyOf": [
                    {"type": "string", "format": "uri"},
                    {
                        "type": "string",
                        "pattern": "^([A-Za-z][A-Za-z0-9\\-_]*:)?[A-Za-z0-9][A-Za-z0-9\\-_]*$",
                    },
                ],
                "description": "Unique IRI identifying the documented resource.",
            }

            schema["properties"]["@type"] = {
                "anyOf": [
                    {"type": "string", "format": "uri"},
                    {
                        "type": "string",
                        "pattern": "^([A-Za-z][A-Za-z0-9\\-_]*:)?[A-Za-z0-9][A-Za-z0-9\\-_]*$",
                    },
                ],
                "description": "IRI of the class the resource belongs to.",
            }

            if not headers:
                logger.warning(
                    f"The CSV file '{input_file}' is empty or missing headers."
                )

            for header in headers:
                # If header is one of the hardcoded properties, prepare examples array
                if header in ["@id", "@type"]:
                    schema["properties"][header]["examples"] = []
                    continue

                # Infer type from data unconditionally
                column_values = [row.get(header) for row in rows]
                inferred_type = _infer_type(column_values)

                prop_def: Dict[str, Any] = {
                    "type": inferred_type,
                    "description": "",
                    "examples": [],
                }

                # Inject ONLY description and conformance from the mapping if present
                if properties_mapping and header in properties_mapping:
                    mapping = properties_mapping[header]

                    if "description" in mapping:
                        prop_def["description"] = mapping["description"]

                    # Ensure mandatory fields are strictly non-null types
                    if mapping.get("conformance") == "mandatory":
                        required_fields.append(header)
                        if (
                            isinstance(prop_def["type"], list)
                            and "null" in prop_def["type"]
                        ):
                            prop_def["type"] = [
                                t for t in prop_def["type"] if t != "null"
                            ]
                            if len(prop_def["type"]) == 1:
                                prop_def["type"] = prop_def["type"][0]

                schema["properties"][header] = prop_def

            schema["required"] = required_fields

            # Only extract the FIRST row of examples from the CSV (if present)
            if rows:
                first_row = rows[0]
                for header in headers:
                    val = first_row.get(header)
                    if val is None or val.strip() == "":
                        schema["properties"][header]["examples"].append(None)
                    else:
                        schema["properties"][header]["examples"].append(val.strip())

            # Cleanup empty example arrays
            for header in headers:
                if not schema["properties"][header].get("examples"):
                    del schema["properties"][header]["examples"]

    except csv.Error as e:
        logger.error(f"Error parsing the CSV file {input_file}: {e}")
        raise ConversionError(f"Failed to parse CSV: {e}", e)
    except OSError as e:
        logger.error(f"OS Error while reading {input_file}: {e}")
        raise ConversionError(f"Failed to read CSV: {e}", e)

    output_path = os.path.join(output_folder, schema_filename)

    try:
        os.makedirs(output_folder, exist_ok=True)
        with open(output_path, mode="w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)

        logger.info(f"Successfully created JSON Schema at: {output_path}")

    except OSError as e:
        logger.error(f"Filesystem error while writing to {output_folder}: {e}")
        raise ConversionError(f"Failed to write JSON: {e}", e)


def json_schema_to_csv(input_file: str, output_folder: str) -> None:
    """
    Reads an OO-LD JSON Schema and rebuilds a CSV file using its aligned array examples.

    Restores the original lines by reading the examples arrays index by index. Null
    values or missing array indices are converted back to empty string cells. The
    resulting CSV file name will always be entirely lowercase.

    Args:
        input_file (str): Path to the input JSON schema file.
        output_folder (str): Directory where the CSV will be saved.

    Raises:
        FileNotFoundError: If the input JSON file does not exist.
        ValueError: If the JSON document lacks a 'properties' key.
        ConversionError: If parsing the JSON or writing the CSV file fails.
    """
    file_path = Path(input_file)

    if not file_path.exists() or not file_path.is_file():
        logger.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(
            f"The specified input JSON file does not exist: {input_file}"
        )

    filename_str = file_path.name
    if filename_str.endswith(".schema.json"):
        file_stem = filename_str.replace(".schema.json", "")
    else:
        file_stem = file_path.stem

    # Ensure the CSV output is always lowercase
    file_stem = file_stem.lower()
    logger.info(f"Reading JSON Schema file: {input_file}")

    try:
        with open(input_file, mode="r", encoding="utf-8") as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {input_file}: {e}")
        raise ConversionError(f"Failed to decode JSON: {e}", e)
    except OSError as e:
        logger.error(f"OS error reading JSON file {input_file}: {e}")
        raise ConversionError(f"Failed to read JSON: {e}", e)

    if "properties" not in schema:
        error_msg = (
            f"Invalid OO-LD Schema: '{input_file}' is missing the 'properties' key."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    properties = schema["properties"]
    headers = list(properties.keys())

    max_rows = 0
    for prop in properties.values():
        examples = prop.get("examples")
        if isinstance(examples, list):
            max_rows = max(max_rows, len(examples))

    output_path = os.path.join(output_folder, f"{file_stem}.csv")

    try:
        os.makedirs(output_folder, exist_ok=True)
        with open(output_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            for i in range(max_rows):
                row = {}
                for header in headers:
                    examples = properties[header].get("examples")
                    if isinstance(examples, list) and i < len(examples):
                        val = examples[i]
                        row[header] = val if val is not None else ""
                    else:
                        row[header] = ""
                writer.writerow(row)

        logger.info(f"Successfully created CSV at: {output_path}")

    except OSError as e:
        logger.error(f"Filesystem error while writing to {output_folder}: {e}")
        raise ConversionError(f"Failed to write CSV: {e}", e)
    except csv.Error as e:
        logger.error(f"Error writing to the CSV file {output_path}: {e}")
        raise ConversionError(f"Failed to write CSV fields: {e}", e)


def process_path(
    input_path: str,
    output_folder: str,
    mode: str,
    base_url: Optional[str] = None,
    properties_mapping: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Processes a single file or a directory of files based on the specified mode.

    Args:
        input_path (str): The path to the input file or directory.
        output_folder (str): The directory where the output files should be saved.
        mode (str): The conversion mode ('csv2json' or 'json2csv').
        base_url (Optional[str]): A base URL for valid IRI generation (csv2json only).
        properties_mapping (Optional[Dict[str, Any]]): Dictionary mapping for OO-LD
            properties injection (csv2json only).

    Raises:
        FileNotFoundError: If the specified input path does not exist.
    """
    path = Path(input_path)

    if not path.exists():
        logger.error(f"Input path not found: {input_path}")
        raise FileNotFoundError(
            f"The specified input path does not exist: {input_path}"
        )

    # Gather files to process
    files_to_process = []
    if path.is_file():
        files_to_process.append(path)
    elif path.is_dir():
        files_to_process = [p for p in path.iterdir() if p.is_file()]

    processed_count = 0

    for file_path in files_to_process:
        ext = file_path.suffix.lower()

        if mode == "csv2json" and ext == ".csv":
            csv_to_json_schema(
                str(file_path), output_folder, base_url, properties_mapping
            )
            processed_count += 1

        elif mode == "json2csv" and ext == ".json":
            json_schema_to_csv(str(file_path), output_folder)
            processed_count += 1

        else:
            if path.is_file():
                # Only warn if the user explicitly provided a single file that we can't process
                logger.warning(
                    f"File '{file_path.name}' unsupported for mode '{mode}'. Skipped."
                )

    if processed_count == 0:
        logger.warning(
            f"No files were processed. Ensure the input contains files matching mode '{mode}'."
        )
    else:
        logger.info(f"Finished processing {processed_count} file(s).")


def main() -> None:
    """
    Main CLI entry point for the OOLD converter.

    Parses arguments from the command line and executes the conversion process.
    """
    parser = argparse.ArgumentParser(
        description="Convert between CSV data and OO-LD JSON Schemas."
    )
    parser.add_argument(
        "input_path",
        help="The path to the input file (CSV/JSON) or directory containing them.",
    )
    parser.add_argument(
        "output_folder", help="The directory where the output files should be saved."
    )
    parser.add_argument(
        "--mode",
        choices=["json2csv", "csv2json"],
        default="json2csv",
        help="Direction of the conversion. Defaults to 'json2csv'.",
    )
    parser.add_argument(
        "--base-url",
        help="Base URL to prepend to the $id field to create a valid IRI.",
    )
    parser.add_argument(
        "--mappings",
        help="Path to a JSON file containing property mappings (e.g., description, range, conformance).",
    )

    args = parser.parse_args()

    properties_mapping = None
    if args.mappings:
        try:
            with open(args.mappings, "r", encoding="utf-8") as f:
                properties_mapping = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load properties mapping from {args.mappings}: {e}")
            sys.exit(1)

    try:
        process_path(
            args.input_path,
            args.output_folder,
            args.mode,
            base_url=args.base_url,
            properties_mapping=properties_mapping,
        )
    except Exception as e:
        logger.critical(f"Process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
