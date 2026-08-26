import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Any, Optional

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
        path: Optional[Path] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        Writes data to a physical file, or returns it as a formatted string.

        Args:
            data (Union[tabular.models.Table, tabular.models.Tables]): The dataset(s) to write.
            path (Optional[Path], optional): The output file path.
                If None, the writer should return the serialized string.
            **kwargs: Format-specific parameters.

        Returns:
            Optional[str]: The serialized string if path is None, else None.
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

    def _ensure_directory(self, path: Optional[Path]) -> None:
        """
        Creates parent directories if they do not exist.

        Args:
            path (Optional[Path]): The full file path being written to.
        """
        if path and not path.parent.exists():
            logger.info(f"Creating missing directories for: {path.parent}")
            path.parent.mkdir(parents=True, exist_ok=True)
