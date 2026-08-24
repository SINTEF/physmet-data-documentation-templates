from typing import List, Dict, Union, Iterator, Any
from pathlib import Path
from .table import Table


class Tables:
    """
    Represents a collection of Table objects (e.g., multiple sheets in an Excel file).
    """

    def __init__(self) -> None:
        """Initializes an empty Tables collection."""
        self._tables: Dict[str, Table] = {}

    def __str__(self) -> str:
        """
        Returns a string representation of all tables in the collection.

        Returns:
            str: The formatted data for all tables.
        """
        if not self.tables:
            return "Empty Tables collection"
        return "\n\n".join(str(t) for t in self.tables)

    def __repr__(self) -> str:
        """
        Returns a detailed string representation of the Tables collection for debugging.

        Returns:
            str: The unambiguous representation of the tables object.
        """
        table_names = [t.name for t in self.tables]
        return f"<Tables(count={len(self.tables)}, names={table_names})>"

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
            return self.tables[key]
        elif isinstance(key, str):
            return self.get_table(key)
        else:
            raise TypeError("Key must be an integer (index) or string (table name).")

    def __iter__(self) -> Iterator[Table]:
        """
        Allows iterating over the tables in the collection.

        Returns:
            Iterator[Table]: An iterator over the tables.
        """
        return iter(self.tables)

    def add_table(self, table: Table) -> None:
        """
        Adds a Table to the collection.

        Args:
            table (Table): The table instance to add.
        """
        self._tables[table.name] = table

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
        if name not in self._tables:
            raise KeyError(f"Table '{name}' not found.")
        return self._tables[name]

    @property
    def tables(self) -> List[Table]:
        """
        Retrieves all tables in the collection.

        Returns:
            List[Table]: A list of all stored Table objects.
        """
        return list(self._tables.values())

    @property
    def first(self) -> Table:
        """
        Convenience property to quickly retrieve the first (or only) table in the collection.

        Returns:
            Table: The first Table added to the collection.

        Raises:
            ValueError: If the collection contains no tables.
        """
        if not self._tables:
            raise ValueError("The Tables collection is empty.")
        return list(self._tables.values())[0]

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
        for table in self.tables:
            for header in table.headers:
                if header not in all_headers:
                    all_headers.append(header)

        merged_table = Table(name=merged_name, headers=all_headers)
        for table in self.tables:
            for row in table.rows:
                row_dict = dict(zip(table.headers, row))
                merged_row = [row_dict.get(h, None) for h in all_headers]
                merged_table.rows.append(merged_row)

        return merged_table

    def append(self, file_path: Union[str, Path], **kwargs: Any) -> None:
        """
        Reads a file and appends its table(s) to this collection.

        Args:
            file_path (Union[str, Path]): The path to the file to read.
            **kwargs: Additional parameters to pass to the parser.
        """
        from tabular import read

        new_tables = read(file_path, **kwargs)
        for t in new_tables.tables:
            self.add_table(t)

    def write(self, file_path: Union[str, Path], **kwargs: Any) -> None:
        """
        Writes the tables to a file.
        If the target format is Excel ('xlsx', 'xlsm'), all tables are written
        as sheets within the same file. Otherwise, a separate file is dynamically
        created for each table using the table's name (e.g., 'output_Sheet1.csv').

        Args:
            file_path (Union[str, Path]): The output destination path.
            **kwargs: Additional parameters to pass to the writer.
        """
        path = Path(file_path)
        fmt = path.suffix.lstrip(".").lower()

        if fmt in ["xlsx", "xlsm"]:
            from tabular import write as tabular_write

            tabular_write(self, path, **kwargs)
        else:
            for table in self.tables:
                # Appends the table name to the file stem to avoid overwriting
                # e.g., output.csv -> output_Sheet1.csv
                table_file_path = path.parent / f"{path.stem}_{table.name}{path.suffix}"
                table.write(table_file_path, **kwargs)
