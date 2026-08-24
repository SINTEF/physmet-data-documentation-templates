import csv
import logging
from pathlib import Path
from typing import Any

import tabular.models
from .base import BaseParser

logger = logging.getLogger(__name__)


class CSVParser(BaseParser):
    """Parses Comma-Separated Values (CSV) files."""

    def parse(
        self, file_path: Path, sniff_dialect: bool = False, **kwargs: Any
    ) -> tabular.models.Tables:
        """
        Parses a CSV file into a Tables collection containing exactly one Table.

        Args:
            file_path (Path): The Path object pointing to the CSV file.
            sniff_dialect (bool, optional): If True, attempts to automatically detect
                the delimiter and quote rules using python's built-in csv.Sniffer.
                Defaults to False.
            **kwargs: Standard parameters accepted by the `csv.reader` (e.g., delimiter,
                quotechar, dialect). Supports custom 'encoding' keyword argument
                (defaults to 'utf-8').

        Returns:
            tabular.models.Tables: A collection containing a single Table representing the CSV.

        Raises:
            FileNotFoundError: If the specified file_path does not exist.
        """
        if not file_path.exists():
            msg = f"CSV file not found: {file_path}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        table_name = file_path.stem
        encoding = kwargs.pop("encoding", "utf-8")

        collection = tabular.models.Tables()
        with open(file_path, mode="r", encoding=encoding) as f:
            # --- Auto-sniffing logic ---
            if sniff_dialect:
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    kwargs["dialect"] = dialect
                    logger.debug(f"Successfully sniffed dialect for {file_path}")
                except csv.Error as e:
                    logger.warning(f"Could not sniff dialect for {file_path}: {e}")
            # ---------------------------

            reader = csv.reader(f, **kwargs)
            try:
                headers = next(reader)
            except StopIteration:
                headers = []

            table = tabular.models.Table(name=table_name, headers=headers)
            for row in reader:
                table.append_row(row)

            collection.add_table(table)

        return collection
