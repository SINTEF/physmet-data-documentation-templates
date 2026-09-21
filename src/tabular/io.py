"""Unified I/O interface for reading and writing tabular datasets."""

from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

import tabular.models.tables

from .registry import get_reader, get_writer, supports_multi_sheet

if TYPE_CHECKING:
    from tabular.models.table import Table
    from tabular.models.tables import Tables

logger = logging.getLogger(__name__)


def read(
    path: Union[str, Path], format: Optional[str] = None, **kwargs: Any
) -> Tables:
    """
    Reads a tabular file and always returns a Tables collection.

    Args:
        path (Union[str, Path]): Path to the file to read.
        format (Optional[str]): Optional format override (e.g. 'csv', 'xlsx').
        **kwargs: Additional keyword arguments passed to the specific reader.

    Returns:
        Tables: A collection representing the parsed dataset(s).

    Raises:
        ValueError: If format cannot be determined or reading fails.
    """
    file_path = Path(path)
    actual_fmt = format or file_path.suffix.lstrip(".").lower()

    if not actual_fmt:
        raise ValueError(
            "Could not determine format from path. "
            "Please explicitly provide 'format'."
        )

    logger.info("Reading file '%s' as format '%s'", file_path, actual_fmt)
    reader = get_reader(actual_fmt)
    return reader.read(file_path, **kwargs)


def write(
    data: Union[Table, Tables],
    path: Optional[Union[str, Path]] = None,
    format: Optional[str] = None,
    **kwargs: Any,
) -> Optional[str]:
    """
    Writes a Table or Tables object to a file or string.

    If a Tables collection is written to a format that does not support
    multiple sheets (e.g., 'csv') and a file path is provided, a directory
    matching the base file name will be created to store individual files.

    Args:
        data (Union[Table, Tables]): The dataset to write.
        path (Optional[Union[str, Path]]): Destination path.
            If None, returns string.
        format (Optional[str]): Format identifier (e.g., 'csv', 'json').
        **kwargs: Additional parameters passed to writer.

    Returns:
        Optional[str]: Serialized string if path is None, else None.
    """
    out_path = Path(path) if path is not None else None

    if out_path is None and format is None:
        raise ValueError(
            "You must specify 'format' (e.g., 'csv', 'json') "
            "when path is None."
        )

    actual_fmt = format or (
        out_path.suffix.lstrip(".").lower() if out_path else ""
    )

    writer = get_writer(actual_fmt)

    if out_path is not None and not supports_multi_sheet(actual_fmt):
        if (
            isinstance(data, tabular.models.tables.Tables)
            and len(data.tables) > 1
        ):
            target_dir = (
                out_path.with_suffix("") if out_path.suffix else out_path
            )

            msg = (
                f"Format '{actual_fmt}' does not support multiple tables. "
                f"A directory '{target_dir}' will be created containing "
                "the individual tables."
            )
            warnings.warn(msg, UserWarning)

            logger.info(
                "Splitting data into individual '%s' files in directory '%s'",
                actual_fmt,
                target_dir,
            )

            target_dir.mkdir(parents=True, exist_ok=True)
            ext = f".{actual_fmt}"

            for table in data.tables:
                table_name = table.name or "sheet"
                split_path = target_dir / f"{table_name}{ext}"
                writer.write(table, split_path, **kwargs)
            return None

    if out_path is not None:
        logger.info(
            "Writing data to '%s' as format '%s'", out_path, actual_fmt
        )
    else:
        logger.info("Serializing data to string as format '%s'", actual_fmt)

    return writer.write(data, out_path, **kwargs)
