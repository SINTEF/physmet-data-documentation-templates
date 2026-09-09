"""
Parser factory for tabular data formats.
"""

import logging
from typing import Any

import tabular.registry

logger = logging.getLogger(__name__)


def get_parser(fmt: str) -> Any:
    """
    Factory function to retrieve the appropriate parser for a file format.
    Delegates to the central registry.

    Args:
        fmt (str): The file extension format (e.g., 'csv', 'xlsx').

    Returns:
        BaseParser: An instantiated parser capable of handling the format.

    Raises:
        ValueError: If the format is unknown or not supported for reading.
    """
    try:
        return tabular.registry.get_parser(fmt)
    except ValueError as e:
        logger.error(str(e))
        raise
