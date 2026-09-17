"""Excel format parser implementation."""

import importlib
import logging
from pathlib import Path
from typing import Any
from zipfile import BadZipFile

import tabular.models
import tabular.utils

from .base import BaseParser

logger = logging.getLogger(__name__)


def _load_openpyxl() -> Any:
    """Safely retrieves the openpyxl module and exception classes if installed."""
    try:
        mod = importlib.import_module("openpyxl")
        exc = importlib.import_module(
            "openpyxl.utils.exceptions"
        ).InvalidFileException
        return mod, exc
    except ImportError:
        return None, Exception


_OPENPYXL, _INVALID_FILE_EXCEPTION = _load_openpyxl()


class ExcelParser(BaseParser):
    """Parses Microsoft Excel (.xlsx, .xlsm) files."""

    def _convert_sheet_to_table(
        self, sheet: Any, sheet_name: str, infer_types: bool
    ) -> tabular.models.Table:
        """Helper to extract rows and headers from an openpyxl sheet."""
        data = list(sheet.values)
        if not data:
            return tabular.models.Table(name=sheet_name, headers=[])

        headers = [str(h) if h is not None else "" for h in data[0]]
        table = tabular.models.Table(name=sheet_name, headers=headers)

        for row in data[1:]:
            table.append_row(list(row))

        if infer_types:
            tabular.utils.infer_and_cast_types(table)

        return table

    def parse(
        self, path: Path, infer_types: bool = True, **kwargs: Any
    ) -> tabular.models.Tables:
        """
        Parses an Excel file into a Tables collection.

        Args:
            path (Path): The Path object pointing to the Excel file.
            infer_types (bool, optional): If True, automatically infers and casts data
                types across all rows. Defaults to True.
            **kwargs: Reserved for future parser-specific configurations.

        Returns:
            tabular.models.Tables: A collection containing one Table per sheet in the workbook.
        """
        if _OPENPYXL is None:
            raise ImportError(
                "The 'openpyxl' package is required to read Excel files. "
                "Install it using 'pip install tabular[excel]' or 'pip install openpyxl'."
            )

        self._validate_path(path)

        try:
            wb = _OPENPYXL.load_workbook(path, data_only=True)
        except (
            BadZipFile,
            _INVALID_FILE_EXCEPTION,
            ValueError,
            KeyError,
        ) as e:
            msg = f"Failed to load Excel file '{path}'. Details: {e}"
            logger.error("%s", msg)
            raise ValueError(msg) from e

        tables = tabular.models.Tables()

        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            table = self._convert_sheet_to_table(
                sheet, sheet_name, infer_types
            )
            tables.append_table(table)

        return tables
