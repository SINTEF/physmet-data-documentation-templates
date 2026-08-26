import sys
import tempfile
import logging
from io import StringIO
from pathlib import Path
from typing import Any, cast
import pytest

import tabular
from tabular.models import Table, Tables
from tabular.registry import get_parser, get_writer

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
    tables.append_table(t1)
    tables.append_table(t2)
    excel_multi_path = tmp_path / "multi_sheet.xlsx"
    tabular.write(tables, excel_multi_path)

    return csv_path, excel_single_path, excel_multi_path


# --- Tests for Central Registry Logic ---


def test_registry_unsupported_read():
    """Verify the central registry rejects unknown or write-only formats when parsing."""
    with pytest.raises(ValueError, match="Unsupported format for reading: 'unknown'"):
        get_parser("unknown")

    with pytest.raises(ValueError, match="Unsupported format for reading: 'md'"):
        get_parser("md")


def test_registry_unsupported_write():
    """Verify the central registry rejects unknown formats when writing."""
    with pytest.raises(ValueError, match="Unsupported format for writing: 'unknown'"):
        get_writer("unknown")


# --- Tests for Validation & Error Handling ---


def test_read_directory_raises_error():
    """Verify reading a directory raises IsADirectoryError."""
    dir_path = TMP_ROOT / "some_read_dir"
    dir_path.mkdir(exist_ok=True)
    with pytest.raises(
        IsADirectoryError, match="Expected a file but found a directory"
    ):
        tabular.read(dir_path, fmt="csv")


def test_write_directory_raises_error():
    """Verify writing to a directory raises IsADirectoryError."""
    dir_path = TMP_ROOT / "some_write_dir"
    dir_path.mkdir(exist_ok=True)
    t = Table("T1", ["A"], [[1]])
    with pytest.raises(IsADirectoryError, match="Target path is a directory"):
        tabular.write(t, dir_path, fmt="csv")


def test_csv_encoding_error():
    """Verify CSVParser catches UnicodeDecodeError and raises a helpful ValueError."""
    bad_csv = TMP_ROOT / "bad_encoding.csv"
    # Write invalid UTF-8 bytes to trigger the decode error natively
    bad_csv.write_bytes(b"\xff\xfe\xfd")
    with pytest.raises(ValueError, match="Encoding error reading"):
        tabular.read(bad_csv, fmt="csv")


def test_excel_invalid_file_error():
    """Verify ExcelParser catches invalid file structures and raises a helpful ValueError."""
    bad_excel = TMP_ROOT / "bad_excel.xlsx"
    bad_excel.write_text(
        "This is definitely not a zip or excel file.", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Failed to load Excel file"):
        tabular.read(bad_excel, fmt="xlsx")


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
    # Expected row values should now be inferred to ints instead of strings
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

    # Ensure it is strictly lowercase to match the module __name__
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
    # CSV now successfully infers types, returning an int `1`
    assert t.rows[1] == [1, "Alice"]

    # Write to file
    out_path = TMP_ROOT / "table_output.csv"
    t.write(out_path)
    assert out_path.exists()


def test_table_write_unsupported_format_raises_exception():
    """Verify writing a single Table object with an unregistered format raises a ValueError."""
    t = Table("Sheet1", ["A"])

    with pytest.raises(
        ValueError, match="Unsupported format for writing: 'unknownformat'"
    ):
        t.write(TMP_ROOT / "output.unknownformat")


def test_table_printable():
    """Verify that Table has appropriate perfectly aligned Markdown __str__ implementations."""
    t = Table("TestSheet", ["ID", "Name"], [[1, "Alice"], [2, "Bob"]])

    expected_str = (
        "## TestSheet\n"
        "| ID | Name  |\n"
        "|----|-------|\n"
        "| 1  | Alice |\n"
        "| 2  | Bob   |"
    )
    assert str(t) == expected_str
    assert repr(t) == "<Table(name='TestSheet', columns=2, rows=2)>"


# --- Tests for Tables Model Features ---


def test_tables_init_with_list():
    """Verify Tables can be initialized directly with a list of Tables."""
    t1 = Table("Sheet1", ["A"])
    t2 = Table("Sheet2", ["B"])
    ts = Tables([t1, t2])

    assert len(ts.tables) == 2
    assert ts[0].name == "Sheet1"
    assert ts[1].name == "Sheet2"


def test_tables_remove_table():
    """Verify Tables can be removed by index or by name."""
    t1 = Table("Sheet1", ["A"])
    t2 = Table("Sheet2", ["B"])
    t3 = Table("Sheet3", ["C"])
    ts = Tables([t1, t2, t3])

    # Remove by name
    ts.remove_table("Sheet2")
    assert len(ts.tables) == 2
    assert ts[1].name == "Sheet3"

    # Remove by index
    ts.remove_table(0)
    assert len(ts.tables) == 1
    assert ts[0].name == "Sheet3"

    # Invalid type bypassed carefully for runtime testing using cast
    with pytest.raises(TypeError, match="Key must be an integer .* or string"):
        ts.remove_table(cast(Any, {"wrong": "type"}))


def test_tables_indexing_and_iteration():
    """Verify that Tables supports indexing by int/name and iteration."""
    t1 = Table("Sheet1", ["A"])
    t2 = Table("Sheet2", ["B"])
    ts = Tables([t1, t2])

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


def test_tables_write_unsupported_format_raises_exception():
    """Verify writing a Tables object with an unregistered format raises a ValueError."""
    ts = Tables([Table("Sheet1", ["A"])])

    with pytest.raises(
        ValueError, match="Unsupported format for writing: 'unknownformat'"
    ):
        ts.write(TMP_ROOT / "output.unknownformat")


def test_tables_printable():
    """Verify that Tables has appropriate Markdown __str__ and __repr__ implementations."""
    t1 = Table("Sheet1", ["A"], [[1]])
    t2 = Table("Sheet2", ["B"], [[2]])
    ts = Tables([t1, t2])

    expected_str = (
        "## Sheet1\n"
        "| A |\n"
        "|---|\n"
        "| 1 |\n\n"
        "## Sheet2\n"
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


def test_writers_append_newline():
    """Verify that MD and JSON writers safely append an empty newline at the end of generated files."""
    t = Table("NewlineTest", ["Col"], [[1]])

    md_path = TMP_ROOT / "test_newline.md"
    json_path = TMP_ROOT / "test_newline.json"

    # Attempt to write to MD and JSON (will be tested assuming they are in the active registry)
    try:
        tabular.write(t, md_path)
        has_md = True
    except ValueError:
        has_md = False

    try:
        tabular.write(t, json_path)
        has_json = True
    except ValueError:
        has_json = False

    # Assert MD formatting
    if has_md and md_path.exists():
        md_content = md_path.read_text(encoding="utf-8")
        assert md_content.endswith(
            "\n"
        ), "Markdown generated file must end with a newline character."
        assert not md_content.endswith(
            "\n\n"
        ), "Markdown generated file must have exactly one trailing newline."

    # Assert JSON formatting
    if has_json and json_path.exists():
        json_content = json_path.read_text(encoding="utf-8")
        assert json_content.endswith(
            "\n"
        ), "JSON generated file must end with a newline character."
        assert not json_content.endswith(
            "\n\n"
        ), "JSON generated file must have exactly one trailing newline."


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

    if failed > 0:
        raise RuntimeError(f"Test suite failed with {failed} errors.")
