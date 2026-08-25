import json
from pathlib import Path
from typing import Union, Any, Optional

import tabular.models
from .base import BaseWriter


class JSONWriter(BaseWriter):
    """Writes tabular data to a JSON format."""

    def write(
        self,
        data: Union[tabular.models.Table, tabular.models.Tables],
        file_path: Optional[Path] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        Writes tabular data to a JSON file as an object mapping table names
        to lists of row dictionaries.

        Args:
            data (Union[tabular.models.Table, tabular.models.Tables]): The dataset(s) to export.
            file_path (Path): Output destination path.
            **kwargs: Standard parameters accepted by `json.dump` (e.g., indent).
                Supports custom 'encoding' keyword argument (defaults to utf-8).
        """
        self._ensure_directory(file_path)
        collection = self._ensure_tables(data)
        out_data = {t.name: t.to_dict_list() for t in collection.tables}

        if file_path is None:
            return str(out_data)

        encoding = kwargs.pop("encoding", "utf-8")
        indent = kwargs.pop("indent", 4)

        with open(file_path, mode="w", encoding=encoding) as f:
            json.dump(out_data, f, indent=indent, **kwargs)
            f.write("\n")
