from typing import List, Union, Iterator, Any, Optional
from pathlib import Path

import tabular.io
import tabular.registry
from .table import Table


class Tables:
    """
    Represents an ordered collection of Table objects.
    """

    def __init__(self) -> None:
        """Initializes an empty Tables collection based on a list."""
        self._tables: List[Table] = []

    def __str__(self) -> str:
        """
        Returns a string representation of all tables in the collection.

        Returns:
            str: The formatted data for all tables.
        """
        if not self._tables:
            return "Empty Tables collection"
        return "\n\n".join(str(t) for t in self._tables)

    def __repr__(self) -> str:
        """
        Returns a detailed string representation of the Tables collection for debugging.

        Returns:
            str: The unambiguous representation of the tables object.
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
            Iterator[Table]: An iterator over the tables.
        """
        return iter(self._tables)

    def add_table(self, table: Table) -> None:
        """
        Adds a Table to the end of the collection.

        Args:
            table (Table): The table instance to add.
        """
        self._tables.append(table)

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

    def merge_all(self, merged_name: str = "MergedTable") -> Table:
        """
        Merges all tables in the collection into a single, combined Table.
        Columns present in some tables but missing in others are filled with None.

        Args:
            merged_name (str, optional): The name for the newly merged table.
                Defaults to "MergedTable".

        Returns:
            Table: A new Table containing all data from all tables in the collection.
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

    def append_file(self, path: Union[str, Path], **kwargs: Any) -> None:
        """
        Reads a file and appends its table(s) to this collection.

        Args:
            path (Union[str, Path]): The path to the file to read.
            **kwargs: Additional parameters to pass to the parser.
        """
        new_tables = tabular.io.read(path, **kwargs)
        for t in new_tables.tables:
            self.add_table(t)

    def write(
        self,
        path: Optional[Union[str, Path]] = None,
        fmt: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        Writes the tables to a file, or serializes them to a string if path is None.
        If the target format supports multi-sheet natively (defined in the registry),
        all tables are written together. Otherwise, a separate file is created for
        each table using the table's name or list index.

        Args:
            path (Optional[Union[str, Path]], optional): The output destination path.
                If None, the collection is serialized and returned as a string.
            fmt (Optional[str], optional): The target format (e.g., 'csv', 'md').
                Required if path is None.
            **kwargs: Additional parameters to pass to the writer.

        Returns:
            Optional[str]: The serialized string if path is None, else None.

        Raises:
            ValueError: If path is None but no format is provided.
        """
        if path is None and fmt is None:
            raise ValueError(
                "You must specify a 'fmt' (e.g., 'csv', 'json') if path is None to parse as a string."
            )

        if path is None:
            return tabular.io.write(self, path=None, fmt=fmt, **kwargs)

        path = Path(path)
        actual_fmt = fmt or path.suffix.lstrip(".").lower()

        # Check the central registry to see if the format supports multiple sheets/tables natively
        if tabular.registry.supports_multi_sheet(actual_fmt):
            return tabular.io.write(self, path, fmt=actual_fmt, **kwargs)
        else:
            # Formats requiring file splitting (e.g. CSV)
            for i, table in enumerate(self._tables):
                suffix = table.name if table.name else str(i)
                table_path = path.parent / f"{path.stem}_{suffix}{path.suffix}"
                table.write(table_path, fmt=actual_fmt, **kwargs)
            return None
