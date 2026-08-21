"""
Tabular Data IO Module
"""

import logging
from pathlib import Path
from typing import Union, Optional, Any
from .models import Table, Tables
from .parsers import get_parser
from .writers import get_writer
from .utils import infer_and_cast_types

logger = logging.getLogger(__name__)


def read(
    file_path: Union[str, Path], fmt: Optional[str] = None, **kwargs: Any
) -> Tables:
    """
    Reads a tabular file and always returns a Tables collection.

    Args:
        file_path (Union[str, Path]): The path to the file to read.
        fmt (str, optional): The format of the file (e.g., 'csv', 'xlsx').
            If None, inferred from the file extension.
        **kwargs: Additional format-specific arguments.

    Returns:
        Tables: A collection of Table objects.

    Raises:
        ValueError: If the file format is unsupported.
        FileNotFoundError: If the specified file_path does not exist.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        msg = f"Cannot read file. Path does not exist: {file_path}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    if fmt is None:
        fmt = file_path.suffix.lstrip(".")

    logger.info(f"Reading file '{file_path}' as format '{fmt}'")
    parser = get_parser(fmt)
    return parser.parse(file_path, **kwargs)


def write(
    data: Union[Table, Tables],
    file_path: Union[str, Path],
    fmt: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Writes a Table or Tables object to a file.

    Args:
        data (Union[Table, Tables]): The tabular data to write.
        file_path (Union[str, Path]): The output destination path.
        fmt (str, optional): The format to save as. If None, inferred from extension.
        **kwargs: Additional format-specific arguments.

    Raises:
        ValueError: If the file format is unsupported.
    """
    file_path = Path(file_path)

    if fmt is None:
        fmt = file_path.suffix.lstrip(".")

    logger.info(f"Writing data to '{file_path}' as format '{fmt}'")
    writer = get_writer(fmt)
    writer.write(data, file_path, **kwargs)


__all__ = ["Table", "Tables", "read", "write", "infer_and_cast_types"]
