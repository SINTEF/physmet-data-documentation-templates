"""
Parser registry and factory for tabular data formats.
"""

import logging
from .base import BaseParser
from .csv_parser import CSVParser
from .excel_parser import ExcelParser

logger = logging.getLogger(__name__)

_PARSER_REGISTRY = {"csv": CSVParser, "xlsx": ExcelParser, "xlsm": ExcelParser}


def get_parser(fmt: str) -> BaseParser:
    """
    Factory function to retrieve the appropriate parser for a file format.

    Args:
        fmt (str): The file extension format (e.g., 'csv', 'xlsx').

    Returns:
        BaseParser: An instantiated parser capable of handling the format.

    Raises:
        ValueError: If the format is unknown or not supported.
    """
    fmt = fmt.lower().strip(".")
    if fmt not in _PARSER_REGISTRY:
        error_msg = f"No parser registered for format: {fmt}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    return _PARSER_REGISTRY[fmt]()
