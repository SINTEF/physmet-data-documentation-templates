from pathlib import Path
from typing import Any, Iterator, List, Optional, Union

import tabular.io
from .table import Table


class Tables:
    """
    Represents an ordered collection of Table objects.

    This class provides a unified interface for managing multiple datasets
    (e.g., sheets in an Excel workbook), allowing for iteration, indexing,
    merging, and batch I/O operations.
    """

    # --- Initialization ---

    def __init__(self, tables: Optional[List[Table]] = None) -> None:
        """
        Initializes a Tables collection.

        Args:
            tables (List[Table], optional): A list of Table objects to initialize with.
        """
        self._tables: List[Table] = []
        if tables:
            for t in tables:
                self.append_table(t)

    # --- Properties ---

    @property
    def tables(self) -> List[Table]:
        """
        Retrieves all tables in the collection.

        Returns:
            List[Table]: A list of all stored Table objects.
        """
        return self._tables

    @property
    def first(self) -> Table:
        """
        Convenience property to quickly retrieve the first table in the collection.

        Returns:
            Table: The first Table added to the collection.

        Raises:
            ValueError: If the collection contains no tables.
        """
        if not self._tables:
            raise ValueError("The Tables collection is empty.")
        return self._tables[0]

    # --- Dunder Methods ---

    def __str__(self) -> str:
        """
        Returns a string representation of all tables in the collection.

        Returns:
            str: The formatted Markdown data for all constituent tables.
        """
        if not self._tables:
            return "Empty Tables collection"
        return "\n\n".join(str(t) for t in self._tables)

    def __repr__(self) -> str:
        """
        Returns a detailed string representation of the Tables collection for debugging.

        Returns:
            str: The unambiguous representation of the tables object detailing count and names.
        """
        table_names = [t.name if t.name else str(i) for i, t in enumerate(self._tables)]
        return f"<Tables(count={len(self._tables)}, names={table_names})>"

    def __getitem__(self, key: Union[int, str]) -> Table:
        """
        Allows indexing to get a table by integer index or by name.

        Args:
            key (Union[int, str]): The integer index or string name of the table.

        Returns:
            Table: The requested table.

        Raises:
            KeyError: If a string key is not found.
            IndexError: If an integer key is out of bounds.
            TypeError: If the key is neither an int nor a str.
        """
        if isinstance(key, int):
            return self._tables[key]
        elif isinstance(key, str):
            return self.get_table(key)
        else:
            raise TypeError("Key must be an integer (index) or string (table name).")

    def __iter__(self) -> Iterator[Table]:
        """
        Allows iterating over the tables in the collection sequentially.

        Returns:
            Iterator[Table]: An iterator yielding each table.
        """
        return iter(self._tables)

    # --- Collection Manipulation ---

    def get_table(self, name: str) -> Table:
        """
        Retrieves a specific table by its name.

        Args:
            name (str): The name of the table to retrieve.

        Returns:
            Table: The matching table.

        Raises:
            KeyError: If a table with the given name does not exist.
        """
        for t in self._tables:
            if t.name == name:
                return t
        raise KeyError(f"Table '{name}' not found.")

    def append_table(self, table: Table) -> None:
        """
        Appends a Table to the end of the collection.

        Args:
            table (Table): The table instance to add.
        """
        self._tables.append(table)

    def remove_table(self, key: Union[int, str]) -> None:
        """
        Removes a table from the collection by its index or name.

        Args:
            key (Union[int, str]): The integer index or string name of the table to remove.

        Raises:
            KeyError: If a table with the given name does not exist.
            IndexError: If an integer key is out of bounds.
            TypeError: If the key is neither an int nor a str.
        """
        if isinstance(key, int):
            del self._tables[key]
        elif isinstance(key, str):
            table_to_remove = self.get_table(key)
            self._tables.remove(table_to_remove)
        else:
            raise TypeError("Key must be an integer (index) or string (table name).")

    def merge_all(self, merged_name: str = "MergedTable") -> Table:
        """
        Merges all tables in the collection into a single, combined Table.

        Columns present in some tables but missing in others are dynamically
        filled with None values.

        Args:
            merged_name (str, optional): The name for the newly merged table.
                Defaults to "MergedTable".

        Returns:
            Table: A new Table containing all row data aligned to a unified schema.
        """
        all_headers: List[str] = []
        for table in self._tables:
            for header in table.headers:
                if header not in all_headers:
                    all_headers.append(header)

        merged_table = Table(name=merged_name, headers=all_headers)
        for table in self._tables:
            for row in table.rows:
                row_dict = dict(zip(table.headers, row))
                merged_row = [row_dict.get(h, None) for h in all_headers]
                merged_table.rows.append(merged_row)

        return merged_table

    # --- I/O & Export Operations ---

    def append_file(self, path: Union[str, Path], **kwargs: Any) -> None:
        """
        Reads a file and appends its table(s) to this collection.

        Args:
            path (Union[str, Path]): The path to the file to read.
            **kwargs: Additional parameters to pass to the underlying parser.
        """
        new_tables = tabular.io.read(path, **kwargs)
        for t in new_tables.tables:
            self.append_table(t)

    def write(
        self,
        path: Optional[Union[str, Path]] = None,
        fmt: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        Writes the tables to a file, or serializes them to a string if path is None.

        Delegates completely to `tabular.io.write`, which handles format resolution,
        registry validation, and automatic file splitting for formats that do not
        support multi-sheet structures natively (e.g., CSV).

        Args:
            path (Optional[Union[str, Path]], optional): The output destination path.
                If None, the collection is serialized and returned as a string.
            fmt (Optional[str], optional): The target format (e.g., 'csv', 'md').
                Required if path is None.
            **kwargs: Additional parameters to pass to the writer.

        Returns:
            Optional[str]: The serialized string if path is None, else None.

        Raises:
            ValueError: If path is None but no format is provided, or if format is unsupported.
        """
        return tabular.io.write(self, path=path, fmt=fmt, **kwargs)
