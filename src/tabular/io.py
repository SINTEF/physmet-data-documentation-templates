import logging
from pathlib import Path
from typing import Union, Optional, Any, TYPE_CHECKING

from .registry import get_parser, get_writer, supports_multi_sheet

if TYPE_CHECKING:
    from .models import Table, Tables

logger = logging.getLogger(__name__)


def read(path: Union[str, Path], fmt: Optional[str] = None, **kwargs: Any) -> "Tables":
    """
    Reads a tabular file and always returns a Tables collection.

    Args:
        path (Union[str, Path]): The path to the file to read.
        fmt (str, optional): The format of the file (e.g., 'csv', 'xlsx').
            If None, inferred from the file extension.
        **kwargs: Additional format-specific arguments.

    Returns:
        Tables: A collection of Table objects.

    Raises:
        ValueError: If the file format is unsupported or cannot be determined.
        FileNotFoundError: If the specified path does not exist.
    """
    path = Path(path)

    if not path.exists():
        msg = f"Cannot read file. Path does not exist: {path}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    actual_fmt = fmt or path.suffix.lstrip(".").lower()

    if not actual_fmt:
        raise ValueError(
            "Could not determine format from path. Please explicitly provide 'fmt'."
        )

    logger.info(f"Reading file '{path}' as format '{actual_fmt}'")

    # get_parser implicitly raises ValueError if format is unregistered
    parser = get_parser(actual_fmt)
    return parser.parse(path, **kwargs)


def write(
    data: Union["Table", "Tables"],
    path: Optional[Union[str, Path]] = None,
    fmt: Optional[str] = None,
    **kwargs: Any,
) -> Optional[str]:
    """
    Writes a Table or Tables object to a file, OR returns it as a formatted string
    if path is None.

    If writing a multi-table collection to a path and the target format does not
    natively support multiple sheets (e.g., CSV), this function will automatically
    split the output, generating a separate file for each table appended with its name.

    Args:
        data (Union[Table, Tables]): The tabular data to write.
        path (Optional[Union[str, Path]], optional): The output destination path.
            If None, the output is returned as a string.
        fmt (Optional[str], optional): The format to save/serialize as.
            If None, inferred from extension (must be provided if path is None).
        **kwargs: Additional format-specific arguments.

    Returns:
        Optional[str]: The serialized string if path is None, else None.

    Raises:
        ValueError: If the file format is unsupported, or if serializing to string without a format.
    """
    if path is None and fmt is None:
        raise ValueError(
            "You must specify a 'fmt' (e.g., 'csv', 'json') if path is None to parse as a string."
        )

    if path is not None:
        path = Path(path)

    actual_fmt: str = fmt or (
        path.suffix.lstrip(".").lower() if path is not None else ""
    )

    if not actual_fmt:
        raise ValueError(
            "Could not determine format from path. Please explicitly provide 'fmt'."
        )

    # get_writer implicitly raises ValueError if format is unregistered
    writer = get_writer(actual_fmt)

    if path is None or supports_multi_sheet(actual_fmt):
        if path is not None:
            logger.info(f"Writing data to '{path}' as format '{actual_fmt}'")
        else:
            logger.info(f"Serializing data to string as format '{actual_fmt}'")
        return writer.write(data, path, **kwargs)

    logger.info(
        f"Splitting data into individual '{actual_fmt}' files at '{path.parent}'"
    )

    # Duck-typing check: if 'data' is a Tables collection, it has a 'tables' list attribute
    if hasattr(data, "tables"):
        for i, table in enumerate(getattr(data, "tables")):
            suffix = getattr(table, "name") or str(i)
            table_path = path.parent / f"{path.stem}_{suffix}{path.suffix}"
            writer.write(table, table_path, **kwargs)
        return None
    else:
        # Fallback for a solitary Table object
        return writer.write(data, path, **kwargs)
