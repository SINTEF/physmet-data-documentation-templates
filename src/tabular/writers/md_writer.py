from pathlib import Path
from typing import Union, Any, Optional

import tabular.models
from .base import BaseWriter


class MDWriter(BaseWriter):
    """Writes tabular data strictly to aligned Markdown tables."""

    def write(
        self,
        data: Union[tabular.models.Table, tabular.models.Tables],
        path: Optional[Path] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        Writes tabular data as visually aligned Markdown.

        Args:
            data (Union[tabular.models.Table, tabular.models.Tables]): The dataset to export.
            path (Optional[Path], optional): Output destination path.
                If None, returns the MD string.
            **kwargs: Supports custom 'encoding' keyword argument (defaults to utf-8).

        Returns:
            Optional[str]: The MD string if path is None, else None.
        """
        collection = self._ensure_tables(data)
        out_str = str(collection)

        if path is None:
            return out_str

        self._ensure_directory(path)
        encoding = kwargs.pop("encoding", "utf-8")

        with open(path, mode="w", encoding=encoding) as f:
            f.write(out_str)
            f.write("\n")

        return None
