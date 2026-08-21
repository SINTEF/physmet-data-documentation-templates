import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Any
from tabular.models import Table, Tables

logger = logging.getLogger(__name__)


class BaseWriter(ABC):
    """
    Abstract base class for all file writers.
    """

    @abstractmethod
    def write(self, data: Union[Table, Tables], file_path: Path, **kwargs: Any) -> None:
        """
        Writes data to a physical file.

        Args:
            data (Union[Table, Tables]): The dataset(s) to write.
            file_path (Path): The output file path.
            **kwargs: Format-specific parameters.
        """
        pass

    def _ensure_tables(self, data: Union[Table, Tables]) -> Tables:
        """
        Helper method to normalize inputs to a Tables object.

        Args:
            data (Union[Table, Tables]): A single table or collection of tables.

        Returns:
            Tables: A valid Tables collection.
        """
        if isinstance(data, Table):
            collection = Tables()
            collection.add_table(data)
            return collection
        return data

    def _ensure_directory(self, file_path: Path) -> None:
        """
        Creates parent directories if they do not exist.

        Args:
            file_path (Path): The full file path being written to.
        """
        if not file_path.parent.exists():
            logger.info(f"Creating missing directories for: {file_path.parent}")
            file_path.parent.mkdir(parents=True, exist_ok=True)
