import logging
from typing import List, Any, Dict, Optional

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
        other_headers_set = set(other.headers)
        self_headers_set = set(self.headers)

        # Identify columns in the other table that do not exist in this one
        new_headers = [h for h in other.headers if h not in self_headers_set]

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

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Converts the table into a list of dictionaries mapping headers to values.

        Returns:
            List[Dict[str, Any]]: A list where each dictionary represents one row.
        """
        return [dict(zip(self.headers, row)) for row in self.rows]
