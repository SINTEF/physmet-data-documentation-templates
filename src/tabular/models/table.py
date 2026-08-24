import logging
from typing import List, Any, Dict, Optional, Union, Iterator
from pathlib import Path

import tabular.io

logger = logging.getLogger(__name__)


class Table:
    """
    Represents a single two-dimensional data dataset with headers and rows.
    """

    def __init__(
        self, name: str, headers: List[str], rows: Optional[List[List[Any]]] = None
    ):
        """
        Initializes a new Table.

        Args:
            name (str): The name of the table (e.g., sheet name, file name).
            headers (List[str]): A list of string headers representing columns.
            rows (List[List[Any]], optional): A list of rows, where each row is a list
                of values. Defaults to an empty list.
        """
        self.name = name
        self.headers = headers
        self.rows = rows if rows is not None else []

    def __str__(self) -> str:
        """
        Returns a string representation of the Table, including headers and all rows.

        Returns:
            str: The formatted table data.
        """
        header_str = " | ".join(str(h) for h in self.headers)
        separator = "-" * len(header_str) if header_str else "-" * 10

        lines = [f"--- Table: {self.name} ---", header_str, separator]
        for row in self.rows:
            lines.append(" | ".join(str(cell) for cell in row))

        return "\n".join(lines)

    def __repr__(self) -> str:
        """
        Returns a detailed string representation of the Table for debugging.

        Returns:
            str: The unambiguous representation of the table object.
        """
        return f"<Table(name='{self.name}', columns={len(self.headers)}, rows={len(self.rows)})>"

    def __getitem__(self, key: Union[int, str]) -> List[Any]:
        """
        Allows indexing into the table to get a row or a column.

        Args:
            key (Union[int, str]): An integer to get a row by index,
                                   or a string to get a column by header name.

        Returns:
            List[Any]: The requested row or column.

        Raises:
            KeyError: If a string key is not found in the headers.
            IndexError: If an integer key is out of bounds for the rows.
            TypeError: If the key is neither an int nor a str.
        """
        if isinstance(key, int):
            return self.rows[key]
        elif isinstance(key, str):
            if key not in self.headers:
                raise KeyError(f"Column '{key}' not found in headers.")
            idx = self.headers.index(key)
            return [row[idx] for row in self.rows]
        else:
            raise TypeError(
                "Key must be an integer (row index) or string (column name)."
            )

    def __iter__(self) -> Iterator[List[Any]]:
        """
        Allows iterating over the rows of the table.

        Returns:
            Iterator[List[Any]]: An iterator over the rows.
        """
        return iter(self.rows)

    def append_row(self, row: List[Any]) -> None:
        """
        Appends a single row to the table sequentially.

        Args:
            row (List[Any]): The data row to append.

        Raises:
            ValueError: If the length of the row does not exactly match the length of the headers.
        """
        if len(row) != len(self.headers):
            msg = f"Row length ({len(row)}) != header length ({len(self.headers)})."
            logger.error(msg)
            raise ValueError(msg)
        self.rows.append(row)

    def append_rows(self, rows: List[List[Any]]) -> None:
        """
        Appends multiple rows to the table sequentially.

        Args:
            rows (List[List[Any]]): A list of data rows to append.

        Raises:
            ValueError: If any row length does not exactly match the header length.
        """
        for row in rows:
            self.append_row(row)

    def append_table(self, other: "Table", merge_headers: bool = False) -> None:
        """
        Appends data from another Table object into this Table.

        Args:
            other (Table): The source Table to append data from.
            merge_headers (bool, optional):
                If True, dynamically adds new columns to this table if they exist in `other`,
                filling existing rows with None for the new columns.
                If False, strictly requires `other`'s headers to be identical to or a subset
                of this table's headers. Defaults to False.

        Raises:
            ValueError: If merge_headers is False and `other` contains columns not present
                        in this table. The operation aborts before modifying any data.
        """
        # Identify columns in the other table that do not exist in this one
        new_headers = [h for h in other.headers if h not in self.headers]

        if new_headers:
            if not merge_headers:
                msg = (
                    f"Failed to append '{other.name}' to '{self.name}'. "
                    f"Unrecognized headers: {new_headers}. Set merge_headers=True to allow."
                )
                logger.error(msg)
                raise ValueError(msg)
            else:
                logger.info(
                    f"Expanding table '{self.name}' schema with headers: {new_headers}"
                )
                # Merge logic: expand current schema
                self.headers.extend(new_headers)
                # Pad all existing rows with None for the newly added columns
                for row in self.rows:
                    row.extend([None] * len(new_headers))

        # Append rows, aligning them to the current headers
        for other_row in other.rows:
            row_dict = dict(zip(other.headers, other_row))
            # Missing subset headers from 'other' gracefully become None
            mapped_row = [row_dict.get(h, None) for h in self.headers]
            self.rows.append(mapped_row)

    def append(
        self, file_path: Union[str, Path], merge_headers: bool = False, **kwargs: Any
    ) -> None:
        """
        Reads a file and appends its tabular data directly into this table.

        Args:
            file_path (Union[str, Path]): The path to the file to read and append.
            merge_headers (bool, optional): If True, dynamically adds new columns. Defaults to False.
            **kwargs: Additional parameters to pass to the parser (e.g., sniff_dialect).
        """
        # Call the module namespace directly
        new_tables = tabular.io.read(file_path, **kwargs)
        for t in new_tables.tables:
            self.append_table(t, merge_headers=merge_headers)

    def write(self, file_path: Union[str, Path], **kwargs: Any) -> None:
        """
        Writes this table directly to a file.

        Args:
            file_path (Union[str, Path]): The output destination path.
            **kwargs: Additional parameters to pass to the writer.
        """
        # Call the module namespace directly
        tabular.io.write(self, file_path, **kwargs)

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Converts the table into a list of dictionaries mapping headers to values.

        Returns:
            List[Dict[str, Any]]: A list where each dictionary represents one row.
        """
        return [dict(zip(self.headers, row)) for row in self.rows]
