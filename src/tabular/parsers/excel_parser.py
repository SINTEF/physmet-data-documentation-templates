import logging
from pathlib import Path
from typing import Any

import tabular.models
import tabular.utils
from .base import BaseParser

logger = logging.getLogger(__name__)


class ExcelParser(BaseParser):
    """Parses Microsoft Excel (.xlsx, .xlsm) files."""

    def parse(
        self, path: Path, infer_types: bool = True, **kwargs: Any
    ) -> tabular.models.Tables:
        """
        Parses an Excel file into a Tables collection.

        Args:
            path (Path): The Path object pointing to the Excel file.
            infer_types (bool, optional): If True, automatically infers and casts data
                types (e.g., formatted string numbers, booleans) across all rows. Defaults to True.
            **kwargs: Reserved for future parser-specific configurations.

        Returns:
            tabular.models.Tables: A collection containing one Table per sheet in the workbook.

        Raises:
            FileNotFoundError: If the specified path does not exist.
            IsADirectoryError: If the path is a directory.
            ImportError: If the 'openpyxl' dependency is missing.
            ValueError: If the file is corrupt, invalid, or unsupported by openpyxl.
        """
        self._validate_path(path)

        try:
            import openpyxl
            from openpyxl.utils.exceptions import InvalidFileException
        except ImportError as e:
            raise ImportError(
                "The 'openpyxl' package is required to read Excel files. "
                "Install it using 'pip install openpyxl'."
            ) from e

        try:
            wb = openpyxl.load_workbook(path, data_only=True)
        except (InvalidFileException, ValueError, Exception) as e:
            # Catches bad zip files, corrupt metadata, and invalid formats
            msg = f"Failed to load Excel file '{path}'. The file may be corrupt or invalid. Details: {e}"
            logger.error(msg)
            raise ValueError(msg) from e

        tables = tabular.models.Tables()

        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            data = list(sheet.values)

            if not data:
                tables.append_table(tabular.models.Table(name=sheet_name, headers=[]))
                continue

            headers = [str(h) if h is not None else "" for h in data[0]]
            table = tabular.models.Table(name=sheet_name, headers=headers)

            for row in data[1:]:
                table.append_row(list(row))

            if infer_types:
                tabular.utils.infer_and_cast_types(table)

            tables.append_table(table)

        return tables
