import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import tabular.models

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """
    Abstract base class for all file parsers.
    """

    @abstractmethod
    def parse(self, path: Path, **kwargs: Any) -> tabular.models.Tables:
        """
        Parses a file from disk into a Tables collection.

        Args:
            path (Path): The Path object pointing to the file to be read.
            **kwargs: Format-specific parameters (e.g., delimiter for CSV).

        Returns:
            tabular.models.Tables: A collection representing the parsed dataset(s).
        """
        pass

    def _validate_path(self, path: Path) -> None:
        """
        Validates that the file path exists and is a file.

        Args:
            path (Path): The file path to validate.

        Raises:
            FileNotFoundError: If the path does not exist.
            IsADirectoryError: If the path is a directory instead of a file.
        """
        if not path.exists():
            msg = f"File not found: {path}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        if path.is_dir():
            msg = f"Expected a file but found a directory: {path}"
            logger.error(msg)
            raise IsADirectoryError(msg)
