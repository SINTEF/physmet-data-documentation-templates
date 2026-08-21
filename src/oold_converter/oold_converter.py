import argparse
import csv
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Configure package-level logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("oold.converter")

# Global schemas and contexts
CONTEXT_URL = "https://raw.githubusercontent.com/SINTEF/physmet-data-documentation-templates/refs/heads/main/context/context.json"
META_SCHEMA = "https://oo-ld.org/latest/meta/oold-meta-schema.json"

# Strict regex for a valid JSON number (RFC 8259)
# Excludes NaN, Inf, -Inf, etc.
JSON_NUMBER_PATTERN = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?$")


IRI_PATTERN = r"^([A-Za-z][A-Za-z0-9\-_]*:)?[A-Za-z0-9][A-Za-z0-9\-_]*$"
HARDCODED_PROPERTIES = ("@id", "@type")


def _iri_property(description: str) -> Dict[str, Any]:
    """Builds the shared JSON Schema shape used for the @id and @type properties."""
    return {
        "anyOf": [
            {"type": "string", "format": "uri"},
            {"type": "string", "pattern": IRI_PATTERN},
        ],
        "description": description,
    }


class ConversionError(Exception):
    """Error raised when conversion between formats fails."""

    pass


def infer_type(
    values: List[Optional[str]], mandatory: bool = False
) -> Union[str, List[str]]:
    """
    Infers the JSON schema data type based on a list of string values.
    Strictly validates numbers against JSON specifications, rejecting NaN/Inf.

    Args:
        values (List[Optional[str]]): The column values extracted from the CSV.
        mandatory (bool): If True, the field is required and its type excludes
            "null", returned as a bare string (e.g. "number"). If False
            (default), the field may be absent/empty and the type allows
            "null", returned as a list (e.g. ["number", "null"]).

    Returns:
        Union[str, List[str]]: The inferred type - a bare string when
        mandatory, otherwise a [type, "null"] list.
    """
    non_nulls = [v.strip() for v in values if v is not None and v.strip() != ""]

    if not non_nulls:
        inferred = "string"
    elif all(v.lower() in ("true", "false") for v in non_nulls):
        inferred = "boolean"
    elif all(JSON_NUMBER_PATTERN.match(v) for v in non_nulls):
        inferred = "number"
    else:
        inferred = "string"

    return inferred if mandatory else [inferred, "null"]


def csv_to_json_schema(
    input_file: Path,
    output_folder: Path,
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
        input_file (Path): Path to the input CSV file.
        output_folder (Path): Directory where the JSON schema will be saved.
        base_url (Optional[str]): A URL to prepend to the `$id` to create a valid IRI.
        properties_mapping (Optional[Dict[str, Any]]): Dictionary mapping column headers
            to their OO-LD metadata definitions.

    Raises:
        FileNotFoundError: If the input CSV file does not exist.
        ConversionError: If parsing the CSV or writing the JSON file fails.
    """
    if not input_file.exists() or not input_file.is_file():
        logger.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(
            f"The specified input CSV file does not exist: {input_file}"
        )

    file_stem = input_file.stem[0].upper() + input_file.stem[1:]
    schema_filename = f"{file_stem}.schema.json"

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
            schema["properties"]["@id"] = _iri_property(
                "Unique IRI identifying the documented resource."
            )
            schema["properties"]["@type"] = _iri_property(
                "IRI of the class the resource belongs to."
            )

            if not headers:
                logger.warning(
                    f"The CSV file '{input_file}' is empty or missing headers."
                )

            for header in headers:
                # If header is one of the hardcoded properties, prepare examples array
                if header in HARDCODED_PROPERTIES:
                    schema["properties"][header]["examples"] = []
                    continue

                # Determine mandatory status from the mapping up front, so infer_type
                # can decide directly whether "null" belongs in the type.
                mapping = properties_mapping.get(header) if properties_mapping else None
                is_mandatory = bool(
                    mapping and mapping.get("conformance") == "mandatory"
                )

                column_values = [row.get(header) for row in rows]
                inferred_type = infer_type(column_values, mandatory=is_mandatory)

                prop_def: Dict[str, Any] = {
                    "type": inferred_type,
                    "description": "",
                    "examples": [],
                }

                # Inject ONLY description and conformance from the mapping if present
                if mapping:
                    if "description" in mapping:
                        prop_def["description"] = mapping["description"]

                    if is_mandatory:
                        required_fields.append(header)

                schema["properties"][header] = prop_def

            schema["required"] = required_fields

            # Only extract the FIRST row of examples from the CSV (if present)
            if rows:
                first_row = rows[0]
                for header in headers:
                    val = first_row.get(header)
                    stripped = val.strip() if val is not None else None
                    schema["properties"][header]["examples"].append(stripped or None)
            else:
                # No rows means every "examples" array is still empty - drop them.
                for header in headers:
                    del schema["properties"][header]["examples"]

    except csv.Error as e:
        logger.error(f"Error parsing the CSV file {input_file}: {e}")
        raise ConversionError(f"Failed to parse CSV: {e}") from e
    except OSError as e:
        logger.error(f"OS Error while reading {input_file}: {e}")
        raise ConversionError(f"Failed to read CSV: {e}") from e

    output_path = output_folder / schema_filename

    try:
        output_folder.mkdir(parents=True, exist_ok=True)
        with open(output_path, mode="w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)

        logger.info(f"Successfully created JSON Schema at: {output_path}")

    except OSError as e:
        logger.error(f"Filesystem error while writing to {output_folder}: {e}")
        raise ConversionError(f"Failed to write JSON: {e}") from e


def json_schema_to_csv(input_file: Path, output_folder: Path) -> None:
    """
    Reads an OO-LD JSON Schema and rebuilds a CSV file using its aligned array examples.

    Restores the original lines by reading the examples arrays index by index. Null
    values or missing array indices are converted back to empty string cells. The
    resulting CSV file name will always be entirely lowercase.

    Args:
        input_file (Path): Path to the input JSON schema file.
        output_folder (Path): Directory where the CSV will be saved.

    Raises:
        FileNotFoundError: If the input JSON file does not exist.
        ValueError: If the JSON document lacks a 'properties' key.
        ConversionError: If parsing the JSON or writing the CSV file fails.
    """
    if not input_file.exists() or not input_file.is_file():
        logger.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(
            f"The specified input JSON file does not exist: {input_file}"
        )

    filename_str = input_file.name
    if filename_str.endswith(".schema.json"):
        file_stem = filename_str.replace(".schema.json", "")
    else:
        file_stem = input_file.stem

    file_stem = file_stem[0].lower() + file_stem[1:]
    logger.info(f"Reading JSON Schema file: {input_file}")

    try:
        with open(input_file, mode="r", encoding="utf-8") as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {input_file}: {e}")
        raise ConversionError(f"Failed to decode JSON: {e}") from e
    except OSError as e:
        logger.error(f"OS error reading JSON file {input_file}: {e}")
        raise ConversionError(f"Failed to read JSON: {e}") from e

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

    output_path = output_folder / f"{file_stem}.csv"

    try:
        output_folder.mkdir(parents=True, exist_ok=True)
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
        raise ConversionError(f"Failed to write CSV: {e}") from e
    except csv.Error as e:
        logger.error(f"Error writing to the CSV file {output_path}: {e}")
        raise ConversionError(f"Failed to write CSV fields: {e}") from e


def process_path(
    input_path: Union[str, Path],
    output_folder: Union[str, Path],
    mode: str,
    base_url: Optional[str] = None,
    properties_mapping: Optional[Dict[str, Any]] = None,
    exclude_files: Optional[List[str]] = None,
) -> None:
    """
    Processes a single file or a directory of files based on the specified mode.

    The function validates the input path and gathers all applicable files for conversion.
    It iterates through the target files, bypassing any filenames explicitly provided in
    the exclusion list. Depending on the selected mode, it routes valid `.csv` files to
    the JSON Schema generator, or `.json` files to the CSV builder. Unsupported file
    formats are safely ignored (logging a warning if a single unsupported file was targeted
    directly), and a final summary log details the total number of successfully processed files.

    Args:
        input_path (Union[str, Path]): The path to the input file or directory.
        output_folder (Union[str, Path]): The directory where the output files should be saved.
        mode (str): The conversion mode ('csv2json' or 'json2csv').
        base_url (Optional[str]): A base URL for valid IRI generation (csv2json only).
        properties_mapping (Optional[Dict[str, Any]]): Dictionary mapping for OO-LD
            properties injection (csv2json only).
        exclude_files (Optional[List[str]]): A list of specific filenames to skip during processing.

    Raises:
        FileNotFoundError: If the specified input path does not exist.
    """
    path = Path(input_path)
    out_folder = Path(output_folder)

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

        if exclude_files and file_path.name in exclude_files:
            logger.info(f"Skipping excluded file: {file_path.name}")
            continue

        if mode == "csv2json" and ext == ".csv":
            csv_to_json_schema(file_path, out_folder, base_url, properties_mapping)
            processed_count += 1

        elif mode == "json2csv" and ext == ".json":
            json_schema_to_csv(file_path, out_folder)
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
        "output_folder",
        help="The directory where the output files should be saved.",
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
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Specific filenames to exclude from processing (e.g. --exclude 'skip.csv' 'ignore.json').",
    )

    args = parser.parse_args()

    properties_mapping = None
    if args.mappings:
        try:
            with open(args.mappings, "r", encoding="utf-8") as f:
                properties_mapping = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load properties mapping from {args.mappings}: {e}")
            sys.exit(1)

    try:
        process_path(
            args.input_path,
            args.output_folder,
            args.mode,
            base_url=args.base_url,
            properties_mapping=properties_mapping,
            exclude_files=args.exclude,
        )
    except Exception as e:
        logger.critical(f"Process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
