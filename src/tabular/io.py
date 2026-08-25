import logging
from pathlib import Path
from typing import Union, Optional, Any, TYPE_CHECKING

# Import from our new central registry
from .registry import get_parser, get_writer

# This prevents circular imports at runtime, but allows linters to see the types
if TYPE_CHECKING:
    from .models import Table, Tables

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
    file_path: Optional[Union[str, Path]] = None,
    fmt: Optional[str] = None,
    **kwargs: Any,
) -> Optional[str]:
    """
    Writes a Table or Tables object to a file, OR returns it as a formatted string
    if file_path is None.

    Args:
        data (Union[Table, Tables]): The tabular data to write.
        file_path (Optional[Union[str, Path]], optional): The output destination path.
            If None, the output is returned as a string.
        fmt (Optional[str], optional): The format to save/serialize as.
            If None, inferred from extension (must be provided if file_path is None).
        **kwargs: Additional format-specific arguments.

    Returns:
        Optional[str]: The serialized string if file_path is None, else None.

    Raises:
        ValueError: If the file format is unsupported, or if serializing to string without a format.
    """
    if file_path is not None:
        file_path = Path(file_path)
        fmt = fmt or file_path.suffix.lstrip(".")
        logger.info(f"Writing data to '{file_path}' as format '{fmt}'")
    else:
        if not fmt:
            raise ValueError(
                "You must provide 'fmt' when returning a string (file_path is None)."
            )
        logger.info(f"Serializing data to string as format '{fmt}'")

    writer = get_writer(fmt)
    return writer.write(data, file_path, **kwargs)
