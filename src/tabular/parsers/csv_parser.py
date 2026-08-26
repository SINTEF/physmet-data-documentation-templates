import csv
import logging
from pathlib import Path
from typing import Any

import tabular.models
import tabular.utils
from .base import BaseParser

logger = logging.getLogger(__name__)


class CSVParser(BaseParser):
    """Parses Comma-Separated Values (CSV) files."""

    def parse(
        self,
        path: Path,
        sniff_dialect: bool = True,
        infer_types: bool = True,
        **kwargs: Any,
    ) -> tabular.models.Tables:
        """
        Parses a CSV file into a Tables collection containing exactly one Table.

        Args:
            path (Path): The Path object pointing to the CSV file.
            sniff_dialect (bool, optional): If True, attempts to automatically detect
                the delimiter and quote rules using python's built-in csv.Sniffer.
                Defaults to True.
            infer_types (bool, optional): If True, automatically infers and casts data
                types (e.g., numbers, booleans) across all rows. Defaults to True.
            **kwargs: Standard parameters accepted by the `csv.reader` (e.g., delimiter,
                quotechar, dialect). Supports custom 'encoding' keyword argument
                (defaults to 'utf-8').

        Returns:
            tabular.models.Tables: A collection containing a single Table representing the CSV.

        Raises:
            FileNotFoundError: If the specified path does not exist.
        """
        if not path.exists():
            msg = f"CSV file not found: {path}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        table_name = path.stem
        encoding = kwargs.pop("encoding", "utf-8")

        collection = tabular.models.Tables()
        with open(path, mode="r", encoding=encoding) as f:
            if sniff_dialect:
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    kwargs["dialect"] = dialect
                    logger.debug(f"Successfully sniffed dialect for {path}")
                except csv.Error as e:
                    logger.warning(f"Could not sniff dialect for {path}: {e}")

            reader = csv.reader(f, **kwargs)
            try:
                headers = next(reader)
            except StopIteration:
                headers = []

            table = tabular.models.Table(name=table_name, headers=headers)
            for row in reader:
                table.append_row(row)

            if infer_types:
                tabular.utils.infer_and_cast_types(table)

            collection.append_table(table)

        return collection
