import re
import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Table

logger = logging.getLogger(__name__)

# Pre-compile regex for performance
_EURO_NUM = re.compile(r"^-?(?:\d{1,3}(?:\.\d{3})*|\d+),\d+$")
_US_NUM = re.compile(r"^-?(?:\d{1,3}(?:,\d{3})*|\d+)\.\d+$")
_INT_NUM = re.compile(r"^-?\d+$")


def infer_and_cast_types(table: Table) -> Table:
    """
    Iterates through a Table and intelligently casts string values to native Python types.

    This function processes every cell in the table. It handles standard integers,
    US-formatted floats (e.g., "1,900.23"), European-formatted floats (e.g., "1.900,23"),
    booleans ("true", "false", "yes", "no"), and empty strings (converted to None).
    Values that do not match these patterns are left as strings.

    Args:
        table (Table): The Table object whose rows should be parsed and cast in-place.

    Returns:
        Table: The same Table instance with its row values updated to native Python types.
    """
    logger.debug(f"Running type inference on table '{table.name}'")

    def parse_value(val: Any) -> Any:
        if not isinstance(val, str):
            return val

        val = val.strip()
        if not val:
            return None

        lower_val = val.lower()
        if lower_val in ("true", "yes"):
            return True
        if lower_val in ("false", "no"):
            return False

        if _EURO_NUM.match(val):
            return float(val.replace(".", "").replace(",", "."))

        if _US_NUM.match(val):
            return float(val.replace(",", ""))

        if _INT_NUM.match(val):
            return int(val)

        return val

    for i, row in enumerate(table.rows):
        table.rows[i] = [parse_value(cell) for cell in row]

    return table
