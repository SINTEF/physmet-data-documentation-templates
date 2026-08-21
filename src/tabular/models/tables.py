from typing import List, Dict
from .table import Table


class Tables:
    """
    Represents a collection of Table objects (e.g., multiple sheets in an Excel file).
    """

    def __init__(self) -> None:
        """Initializes an empty Tables collection."""
        self._tables: Dict[str, Table] = {}

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
