import csv
import io
from pathlib import Path
from typing import Union, Any, Optional

import tabular.models
from .base import BaseWriter


class CSVWriter(BaseWriter):
    """Writes tabular data to a CSV format."""

    def write(
        self,
        data: Union["tabular.models.Table", "tabular.models.Tables"],
        path: Optional[Path] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        Writes tabular data to a CSV file or string. If a multiple-table collection
        is provided, it automatically merges them into a single table prior to writing.

        Args:
            data (Union[tabular.models.Table, tabular.models.Tables]): The dataset to export.
            path (Optional[Path], optional): Output destination path.
                If None, returns the CSV string.
            **kwargs: Standard parameters accepted by the `csv.writer` (e.g., delimiter).
                Supports custom 'encoding' keyword argument (defaults to utf-8).

        Returns:
            Optional[str]: The CSV string if path is None, else None.
        """
        if path is not None:
            self._ensure_directory(path)

        table = (
            data.merge_all()
            if (isinstance(data, tabular.models.Tables) and len(data.tables) > 1)
            else (data.first if isinstance(data, tabular.models.Tables) else data)
        )

        encoding = kwargs.pop("encoding", "utf-8")

        if path is None:
            f = io.StringIO()
        else:
            f = open(path, mode="w", newline="", encoding=encoding)

        try:
            writer = csv.writer(f, **kwargs)
            writer.writerow(table.headers)
            writer.writerows(table.rows)

            if path is None and isinstance(f, io.StringIO):
                return f.getvalue()
        finally:
            if path is not None:
                f.close()
        return None
