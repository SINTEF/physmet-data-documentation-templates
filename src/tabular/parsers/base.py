from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import tabular.models


class BaseParser(ABC):
    """
    Abstract base class for all file parsers.
    """

    @abstractmethod
    def parse(self, file_path: Path, **kwargs: Any) -> tabular.models.Tables:
        """
        Parses a file from disk into a Tables collection.

        Args:
            file_path (Path): The Path object pointing to the file to be read.
            **kwargs: Format-specific parameters (e.g., delimiter for CSV).

        Returns:
            tabular.models.Tables: A collection representing the parsed dataset(s).
        """
        pass
