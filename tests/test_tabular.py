import sys
import tempfile
import logging
from io import StringIO
from pathlib import Path
import pytest

import tabular
from tabular.models import Table, Tables

# --- Global Test Environment Setup ---

# Create a root temporary directory for the session
_SESSION_TMP_DIR = tempfile.TemporaryDirectory()
TMP_ROOT = Path(_SESSION_TMP_DIR.name)


def provision_test_data(tmp_path: Path):
    """Helper function to populate a test's temporary directory with sample data."""
    # 1. Create a dummy CSV file
    csv_path = tmp_path / "single_table.csv"
    csv_path.write_text("ID,Name\n1,Alice\n2,Bob", encoding="utf-8")

    # 2. Create a dummy single-sheet Excel file
    t_single = Table(name="SingleSheet", headers=["Col1", "Col2"], rows=[["A", "B"]])
    excel_single_path = tmp_path / "single_sheet.xlsx"
    tabular.write(t_single, excel_single_path)

    # 3. Create a dummy multi-sheet Excel file
    t1 = Table(name="Sheet1", headers=["X", "Y"], rows=[[10, 20]])
    t2 = Table(name="Sheet2", headers=["X", "Z"], rows=[[10, 30]])
    tables = Tables()
    tables.add_table(t1)
    tables.add_table(t2)
    excel_multi_path = tmp_path / "multi_sheet.xlsx"
    tabular.write(tables, excel_multi_path)

    return csv_path, excel_single_path, excel_multi_path


# --- Tests for Parsers ---


def test_csv_returns_tables_collection():
    """Verify CSV files always return a Tables object for predictability."""
    csv_path, _, _ = provision_test_data(TMP_ROOT)

    result = tabular.read(csv_path)

    assert isinstance(result, Tables), "CSV parser did not return a Tables object."
    assert len(result.tables) == 1

    # Verify .first property convenience behavior
    first_table = result.first
    assert first_table.headers == ["ID", "Name"]
    # UPDATED: Expected row values should now be inferred to ints instead of strings
    assert first_table.rows == [[1, "Alice"], [2, "Bob"]]


def test_excel_single_sheet_returns_tables_collection():
    """Verify single-sheet Excel files always return a Tables object."""
    _, excel_single_path, _ = provision_test_data(TMP_ROOT)

    result = tabular.read(excel_single_path)

    assert isinstance(result, Tables)
    assert len(result.tables) == 1
    assert result.first.name == "SingleSheet"


def test_excel_multi_sheet_returns_tables_collection():
    """Verify multi-sheet Excel files return a populated Tables object."""
    _, _, excel_multi_path = provision_test_data(TMP_ROOT)

    result = tabular.read(excel_multi_path)

    assert isinstance(result, Tables)
    assert len(result.tables) == 2
    assert "Sheet1" in [t.name for t in result.tables]


# --- Tests for Table Model Appending, Logging & Features ---


def test_append_table_strict_rejection():
    """Test append_table fails explicitly if target lacks source headers and merge_headers=False."""
    t1 = Table("Target", ["A", "B"], [[1, 2]])
    t2 = Table("Source", ["A", "C"], [[3, 4]])

    with pytest.raises(ValueError, match="Unrecognized headers: \\['C'\\]"):
        t1.append_table(t2, merge_headers=False)

    # Ensure atomic behavior: no data was corrupted due to failure
    assert len(t1.rows) == 1
    assert t1.headers == ["A", "B"]


def test_append_table_merge_success():
    """Test append_table expands columns and inserts None when merge_headers=True."""
    t1 = Table("Target", ["A", "B"], [[1, 2]])
    t2 = Table("Source", ["A", "C"], [[3, 4]])

    t1.append_table(t2, merge_headers=True)

    assert set(t1.headers) == {"A", "B", "C"}
    # Original row padded with None for new 'C' column
    assert t1.rows[0] == [1, 2, None]
    # Appended row padded with None for existing 'B' column
    assert t1.rows[1] == [3, None, 4]


def test_append_table_logs_error():
    """A mismatch in headers when merging=False logs a specific error."""
    t1 = Table("Target", ["A", "B"], [[1, 2]])
    t2 = Table("Source", ["A", "C"], [[3, 4]])

    # Manually capture logs without relying on pytest caplog fixture
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)

    # FIX: Ensure it is strictly lowercase to match the module __name__
    logger = logging.getLogger("tabular.models.table")

    # Explicitly set the log level to bypass pytest's default filtering
    old_level = logger.level
    logger.setLevel(logging.ERROR)
    logger.addHandler(handler)

    try:
        with pytest.raises(ValueError):
            t1.append_table(t2, merge_headers=False)

        assert "Unrecognized headers:" in log_capture.getvalue()
    finally:
        logger.removeHandler(handler)
        # Restore the original log level
        logger.setLevel(old_level)


def test_csv_parser_sniff_warns_on_fail():
    """Sniffing an empty/invalid file logs a warning gracefully."""
    bad_csv = TMP_ROOT / "empty.csv"

    # Use a genuinely empty file to absolutely guarantee a csv.Error
    bad_csv.write_text("", encoding="utf-8")

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)

    logger = logging.getLogger("tabular.parsers.csv_parser")
    # Explicitly set the log level for this test to bypass pytest's default filtering
    old_level = logger.level
    logger.setLevel(logging.WARNING)
    logger.addHandler(handler)

    try:
        tabular.read(bad_csv, sniff_dialect=True)
        assert "Could not sniff dialect" in log_capture.getvalue()
    finally:
        logger.removeHandler(handler)
        # Restore the original log level to avoid leaking state to other tests
        logger.setLevel(old_level)


def test_table_indexing_and_iteration():
    """Verify that Table supports row indexing, column indexing, and iteration."""
    t = Table("Test", ["ID", "Name"], [[1, "Alice"], [2, "Bob"]])

    # Row indexing
    assert t[0] == [1, "Alice"]

    # Column indexing
    assert t["Name"] == ["Alice", "Bob"]

    # Iteration
    rows = [row for row in t]
    assert len(rows) == 2
    assert rows[1] == [2, "Bob"]

    with pytest.raises(KeyError):
        _ = t["UnknownColumn"]


def test_table_append_from_file_and_write():
    """Verify that Table can append data directly from a file and write itself to disk."""
    csv_path, _, _ = provision_test_data(TMP_ROOT)

    t = Table("Base", ["ID", "Name"], [[99, "Zero"]])

    # Append from file
    t.append_file(csv_path)

    assert len(t.rows) == 3
    # UPDATED: CSV now successfully infers types, returning an int `1`
    assert t.rows[1] == [1, "Alice"]

    # Write to file
    out_path = TMP_ROOT / "table_output.json"
    t.write(out_path)
    assert out_path.exists()


def test_table_printable():
    """Verify that Table has appropriate perfectly aligned Markdown __str__ implementations."""
    t = Table("TestSheet", ["ID", "Name"], [[1, "Alice"], [2, "Bob"]])

    # FIX: Updated to match the new Markdown rendering
    expected_str = (
        "## TestSheet\n\n"
        "| ID | Name  |\n"
        "|----|-------|\n"
        "| 1  | Alice |\n"
        "| 2  | Bob   |"
    )
    assert str(t) == expected_str
    assert repr(t) == "<Table(name='TestSheet', columns=2, rows=2)>"


# --- Tests for Tables Model Features ---


def test_tables_indexing_and_iteration():
    """Verify that Tables supports indexing by int/name and iteration."""
    ts = Tables()
    t1 = Table("Sheet1", ["A"])
    t2 = Table("Sheet2", ["B"])
    ts.add_table(t1)
    ts.add_table(t2)

    # Indexing
    assert ts[0] == t1
    assert ts["Sheet2"] == t2

    # Iteration
    table_names = [table.name for table in ts]
    assert table_names == ["Sheet1", "Sheet2"]

    with pytest.raises(KeyError):
        _ = ts["UnknownSheet"]


def test_tables_append_from_file_and_write():
    """Verify that Tables can append data from a file and write to disk dynamically."""
    _, excel_single_path, _ = provision_test_data(TMP_ROOT)

    ts = Tables()
    ts.append_file(excel_single_path)

    assert len(ts.tables) == 1
    assert ts[0].name == "SingleSheet"

    # Write to a format that requires splitting (CSV)
    split_csv_path = TMP_ROOT / "output.csv"
    ts.write(split_csv_path)
    # The file should be saved with the table name appended
    expected_split_file = TMP_ROOT / "output_SingleSheet.csv"
    assert expected_split_file.exists()


def test_tables_printable():
    """Verify that Tables has appropriate Markdown __str__ and __repr__ implementations."""
    ts = Tables()
    t1 = Table("Sheet1", ["A"], [[1]])
    t2 = Table("Sheet2", ["B"], [[2]])
    ts.add_table(t1)
    ts.add_table(t2)

    # FIX: Updated to match the new Markdown rendering for multiple tables
    expected_str = (
        "## Sheet1\n\n"
        "| A |\n"
        "|---|\n"
        "| 1 |\n\n"
        "## Sheet2\n\n"
        "| B |\n"
        "|---|\n"
        "| 2 |"
    )

    assert str(ts) == expected_str
    assert repr(ts) == "<Tables(count=2, names=['Sheet1', 'Sheet2'])>"


# --- Tests for Writers ---


def test_csv_write_implicitly_merges_tables():
    """When a multi-table Tables object is passed to CSVWriter, it should merge them natively."""
    _, _, excel_multi_path = provision_test_data(TMP_ROOT)

    out_csv = TMP_ROOT / "merged_output.csv"

    # Read multi-sheet (Returns Tables)
    tables = tabular.read(excel_multi_path)

    # Write to CSV via standard writer (implicitly merges during output)
    tabular.write(tables, out_csv)

    # Read back to verify
    merged_table = tabular.read(out_csv).first
    assert set(merged_table.headers) == {"X", "Y", "Z"}


# --- Standalone Execution Logic ---

if __name__ == "__main__":
    print("Running Tabular Data IO tests standalone...\n")
    test_functions = [
        obj
        for name, obj in globals().items()
        if callable(obj) and name.startswith("test_")
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        sys.stdout.write(f"Running {test_func.__name__} ... ")
        try:
            test_func()
            print("PASSED")
            passed += 1
        except Exception as e:
            print(f"FAILED\n  -> {type(e).__name__}: {e}")
            failed += 1

    print("\n--- Test Run Summary ---")
    print(f"Total: {passed + failed} | Passed: {passed} | Failed: {failed}")

    # Environment-agnostic failure handling:
    # This will fail standard CI/CD pipelines but won't crash interactive IPython kernels.
    if failed > 0:
        raise RuntimeError(f"Test suite failed with {failed} errors.")
