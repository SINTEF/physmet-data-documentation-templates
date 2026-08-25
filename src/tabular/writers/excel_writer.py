import openpyxl
from pathlib import Path
from typing import Union, Any, Optional

# Import the namespace instead of strictly extracting classes
import tabular.models
from .base import BaseWriter


class ExcelWriter(BaseWriter):
    """Writes tabular data to an Excel (.xlsx) workbook."""

    def write(
        self,
        data: Union[tabular.models.Table, tabular.models.Tables],
        file_path: Optional[Path] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        Writes data to an Excel workbook. It creates one spreadsheet per Table in
        the provided collection.

        Args:
            data (Union[tabular.models.Table, tabular.models.Tables]): The dataset(s) to export.
            file_path (Optional[Path], optional): Output destination path.
            **kwargs: Reserved for future Excel-specific parameters.

        Returns:
            None (Excel files cannot be parsed as strings in this library).

        Raises:
            ValueError: If file_path is None, as binary formats cannot be cleanly serialized to standard strings.
        """
        if file_path is None:
            raise ValueError(
                "Excel format is binary and cannot be generated as a string. You must provide a file_path."
            )

        self._ensure_directory(file_path)
        collection = self._ensure_tables(data)
        wb = openpyxl.Workbook()

        if "Sheet" in wb.sheetnames:
            wb.remove(wb["Sheet"])

        for i, table in enumerate(collection.tables):
            sheet_title = (table.name or f"Sheet{i}")[:31]
            ws = wb.create_sheet(title=sheet_title)
            ws.append(table.headers)
            for row in table.rows:
                ws.append(row)

        wb.save(file_path)
        return None
