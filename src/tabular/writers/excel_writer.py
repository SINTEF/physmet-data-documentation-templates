import openpyxl
from pathlib import Path
from typing import Union, Any

# Import the namespace instead of strictly extracting classes
import tabular.models
from .base import BaseWriter


class ExcelWriter(BaseWriter):
    """Writes tabular data to an Excel (.xlsx) workbook."""

    def write(
        self,
        data: Union[tabular.models.Table, tabular.models.Tables],
        file_path: Path,
        **kwargs: Any,
    ) -> None:
        """
        Writes data to an Excel workbook. It creates one spreadsheet per Table in
        the provided collection.

        Args:
            data (Union[tabular.models.Table, tabular.models.Tables]): The dataset(s) to export.
            file_path (Path): Output destination path.
            **kwargs: Reserved for future Excel-specific parameters.
        """
        self._ensure_directory(file_path)
        collection = self._ensure_tables(data)
        wb = openpyxl.Workbook()

        # Remove the default empty sheet initialized by openpyxl
        if "Sheet" in wb.sheetnames:
            wb.remove(wb["Sheet"])

        for table in collection.tables:
            # Excel limits sheet names to 31 characters
            ws = wb.create_sheet(title=table.name[:31])
            ws.append(table.headers)
            for row in table.rows:
                ws.append(row)

        wb.save(file_path)
