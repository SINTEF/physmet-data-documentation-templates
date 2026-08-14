import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

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


def csv_to_json_schema(input_file: str, output_folder: str) -> None:
    """Reads a CSV file and generates an OO-LD JSON Schema preserving whole-line examples."""
    file_path = Path(input_file)

    if not file_path.exists() or not file_path.is_file():
        logger.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(
            f"The specified input CSV file does not exist: {input_file}"
        )

    file_stem = file_path.stem

    schema: Dict[str, Any] = {
        "$schema": META_SCHEMA,
        "$id": f"{file_stem}.schema.json",
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

            if not headers:
                logger.warning(
                    f"The CSV file '{input_file}' is empty or missing headers."
                )

            for header in headers:
                schema["properties"][header] = {
                    "type": ["string", "null"],
                    "description": "",
                    "examples": [],
                }

            rows = list(reader)
            for row in rows:
                for header in headers:
                    val = row.get(header)
                    if val is None or val.strip() == "":
                        schema["properties"][header]["examples"].append(None)
                    else:
                        schema["properties"][header]["examples"].append(val.strip())

            for header in headers:
                # Remove the examples key entirely if the array is empty
                if not schema["properties"][header].get("examples"):
                    del schema["properties"][header]["examples"]

    except csv.Error as e:
        logger.error(f"Error parsing the CSV file {input_file}: {e}")
        raise ConversionError(f"Failed to parse CSV: {e}", e)
    except OSError as e:
        logger.error(f"OS Error while reading {input_file}: {e}")
        raise ConversionError(f"Failed to read CSV: {e}", e)

    output_path = os.path.join(output_folder, f"{file_stem}.schema.json")

    try:
        os.makedirs(output_folder, exist_ok=True)
        with open(output_path, mode="w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)

        logger.info(f"Successfully created JSON Schema at: {output_path}")

    except OSError as e:
        logger.error(f"Filesystem error while writing to {output_folder}: {e}")
        raise ConversionError(f"Failed to write JSON: {e}", e)


def json_schema_to_csv(input_file: str, output_folder: str) -> None:
    """Reads an OO-LD JSON Schema and rebuilds a CSV file using its aligned array examples."""
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


def process_path(input_path: str, output_folder: str, mode: str) -> None:
    """
    Processes a single file or a directory of files based on the specified mode.
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
            csv_to_json_schema(str(file_path), output_folder)
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
    """Main CLI entry point for the OOLD converter."""
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

    args = parser.parse_args()

    try:
        process_path(args.input_path, args.output_folder, args.mode)
    except Exception as e:
        logger.critical(f"Process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
