import openpyxl
import logging
from pathlib import Path
from typing import Any

# Import the namespace instead of strictly extracting classes
import tabular.models
from .base import BaseParser

logger = logging.getLogger(__name__)


class ExcelParser(BaseParser):
    """Parses Microsoft Excel (.xlsx, .xlsm) files."""

    def parse(self, file_path: Path, **kwargs: Any) -> tabular.models.Tables:
        """
        Parses an Excel file into a Tables collection.

        Args:
            file_path (Path): The Path object pointing to the Excel file.
            **kwargs: Reserved for future parser-specific configurations.

        Returns:
            tabular.models.Tables: A collection containing one Table per sheet in the workbook.

        Raises:
            FileNotFoundError: If the specified file_path does not exist.
        """
        if not file_path.exists():
            msg = f"Excel file not found: {file_path}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        wb = openpyxl.load_workbook(file_path, data_only=True)
        tables = tabular.models.Tables()

        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            data = list(sheet.values)

            if not data:
                # Handle empty sheets by appending an empty table
                tables.add_table(tabular.models.Table(name=sheet_name, headers=[]))
                continue

            headers = [str(h) if h is not None else "" for h in data[0]]
            table = tabular.models.Table(name=sheet_name, headers=headers)

            for row in data[1:]:
                table.append_row(list(row))

            tables.add_table(table)

        return tables
