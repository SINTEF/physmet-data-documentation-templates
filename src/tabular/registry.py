"""
Central Format Registry
"""

import logging
from typing import Dict, Any

# Parsers
from tabular.parsers.csv_parser import CSVParser
from tabular.parsers.excel_parser import ExcelParser

# Writers
from tabular.writers.csv_writer import CSVWriter
from tabular.writers.excel_writer import ExcelWriter
from tabular.writers.json_writer import JSONWriter
from tabular.writers.md_writer import MDWriter

logger = logging.getLogger(__name__)

# The single source of truth for format routing and capabilities.
# To add a new format, simply add a new key here.
FORMAT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "csv": {"parser": CSVParser, "writer": CSVWriter, "multi_sheet": False},
    "xlsx": {"parser": ExcelParser, "writer": ExcelWriter, "multi_sheet": True},
    "xlsm": {"parser": ExcelParser, "writer": ExcelWriter, "multi_sheet": True},
    "md": {"parser": None, "writer": MDWriter, "multi_sheet": True},
    "json": {"parser": None, "writer": JSONWriter, "multi_sheet": True},
}


def get_parser(fmt: str) -> Any:
    """
    Retrieves the appropriate parser instance for the given format.

    Args:
        fmt (str): The file format extension (e.g., 'csv').

    Returns:
        BaseParser: An instance of the corresponding parser.

    Raises:
        ValueError: If the format is not supported for reading.
    """
    entry = FORMAT_REGISTRY.get(fmt.lower())
    if not entry or not entry.get("parser"):
        raise ValueError(f"Unsupported format for reading: '{fmt}'")
    return entry["parser"]()


def get_writer(fmt: str) -> Any:
    """
    Retrieves the appropriate writer instance for the given format.

    Args:
        fmt (str): The file format extension (e.g., 'csv').

    Returns:
        BaseWriter: An instance of the corresponding writer.

    Raises:
        ValueError: If the format is not supported for writing.
    """
    entry = FORMAT_REGISTRY.get(fmt.lower())
    if not entry or not entry.get("writer"):
        raise ValueError(f"Unsupported format for writing: '{fmt}'")
    return entry["writer"]()


def supports_multi_sheet(fmt: str) -> bool:
    """
    Checks if a format natively supports multiple tables (sheets) in a single file.

    Args:
        fmt (str): The file format extension.

    Returns:
        bool: True if the format supports multiple tables natively, False otherwise.
    """
    entry = FORMAT_REGISTRY.get(fmt.lower())
    if not entry:
        return False
    return entry.get("multi_sheet", False)
