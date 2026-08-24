import csv
from pathlib import Path
from typing import Union, Any

# Import the namespace instead of strictly extracting classes
import tabular.models
from .base import BaseWriter


class CSVWriter(BaseWriter):
    """Writes tabular data to a CSV format."""

    def write(
        self,
        data: Union[tabular.models.Table, tabular.models.Tables],
        file_path: Path,
        **kwargs: Any,
    ) -> None:
        """
        Writes tabular data to a CSV file. If a multiple-table collection is provided,
        it automatically merges them into a single table prior to writing.

        Args:
            data (Union[tabular.models.Table, tabular.models.Tables]): The dataset to export.
            file_path (Path): Output destination path.
            **kwargs: Standard parameters accepted by the `csv.writer` (e.g., delimiter).
                Supports custom 'encoding' keyword argument (defaults to utf-8).
        """
        self._ensure_directory(file_path)

        if isinstance(data, tabular.models.Tables):
            # Resolve to a single dataset for CSV
            table = data.merge_all() if len(data.tables) > 1 else data.first
        else:
            table = data

        encoding = kwargs.pop("encoding", "utf-8")
        with open(file_path, mode="w", newline="", encoding=encoding) as f:
            writer = csv.writer(f, **kwargs)
            writer.writerow(table.headers)
            writer.writerows(table.rows)
