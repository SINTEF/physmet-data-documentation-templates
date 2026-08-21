"""
Writer registry and factory for tabular data formats.
"""

import logging
from .base import BaseWriter
from .csv_writer import CSVWriter
from .json_writer import JSONWriter
from .excel_writer import ExcelWriter

logger = logging.getLogger(__name__)

_WRITER_REGISTRY = {
    "csv": CSVWriter,
    "json": JSONWriter,
    "xlsx": ExcelWriter,
}


def get_writer(fmt: str) -> BaseWriter:
    """
    Factory function to retrieve the appropriate writer for a file format.

    Args:
        fmt (str): The target file extension format (e.g., 'csv', 'xlsx').

    Returns:
        BaseWriter: An instantiated writer capable of outputting the format.

    Raises:
        ValueError: If the format is unknown or not supported.
    """
    fmt = fmt.lower().strip(".")
    if fmt not in _WRITER_REGISTRY:
        error_msg = f"No writer registered for format: {fmt}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    return _WRITER_REGISTRY[fmt]()
