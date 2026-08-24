import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Any

# Import the namespace instead of strictly extracting classes
import tabular.models

logger = logging.getLogger(__name__)


class BaseWriter(ABC):
    """
    Abstract base class for all file writers.
    """

    @abstractmethod
    def write(
        self,
        data: Union[tabular.models.Table, tabular.models.Tables],
        file_path: Path,
        **kwargs: Any,
    ) -> None:
        """
        Writes data to a physical file.

        Args:
            data (Union[tabular.models.Table, tabular.models.Tables]): The dataset(s) to write.
            file_path (Path): The output file path.
            **kwargs: Format-specific parameters.
        """
        pass

    def _ensure_tables(
        self, data: Union[tabular.models.Table, tabular.models.Tables]
    ) -> tabular.models.Tables:
        """
        Helper method to normalize inputs to a Tables object.

        Args:
            data (Union[tabular.models.Table, tabular.models.Tables]): A single table or collection of tables.

        Returns:
            tabular.models.Tables: A valid Tables collection.
        """
        # Because we imported the namespace, we can safely use isinstance without crashing at import time
        if isinstance(data, tabular.models.Table):
            collection = tabular.models.Tables()
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
