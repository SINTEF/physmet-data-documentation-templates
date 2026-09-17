"""Unit test suite for the tabular library."""

import logging
import sys
import tempfile
from io import StringIO
from pathlib import Path
from typing import Any, cast

import pytest

import tabular
from tabular.models import Table, Tables
from tabular.registry import get_parser, get_writer

# --- Global Test Environment Setup ---


# The session temporary directory is kept strictly for WRITING test outputs.
def get_tmp_root() -> Path:
    """Creates a temporary path for writing test outputs safely."""
    temp_dir = tempfile.mkdtemp()
    return Path(temp_dir)


TMP_ROOT = get_tmp_root()

# Hardcoded paths to the new unified persistent test data
DATA_DIR = Path("./tests/data/tabular")
FILE_CSV = DATA_DIR / "complex_data.csv"
FILE_EXCEL = DATA_DIR / "complex_data.xlsx"


# --- Tests for Central Registry Logic ---


def test_registry_unsupported_read():
    """Verify registry rejects unknown/write-only formats on parse."""
    with pytest.raises(
        ValueError, match="Unsupported format for reading: 'unknown'"
    ):
        get_parser("unknown")

    with pytest.raises(
        ValueError, match="Unsupported format for reading: 'md'"
    ):
        get_parser("md")


def test_registry_unsupported_write():
    """Verify registry rejects unknown formats when writing."""
    with pytest.raises(
        ValueError, match="Unsupported format for writing: 'unknown'"
    ):
        get_writer("unknown")


# --- Tests for Validation & Error Handling ---


def test_read_directory_raises_error():
    """Verify reading a directory raises IsADirectoryError."""
    with pytest.raises(
        IsADirectoryError, match="Expected a file but found a directory"
    ):
        tabular.read(DATA_DIR, fmt="csv")


def test_write_directory_raises_error():
    """Verify writing to a directory raises IsADirectoryError."""
    t = Table("T1", ["A"], [[1]])
    with pytest.raises(IsADirectoryError, match="Target path is a directory"):
        tabular.write(t, DATA_DIR, fmt="csv")


def test_csv_encoding_error():
    """Verify CSVParser catches UnicodeDecodeError and raises ValueError."""
    bad_csv = TMP_ROOT / "bad_encoding.csv"
    # Write invalid UTF-8 bytes to trigger the decode error natively
    bad_csv.write_bytes(b"\xff\xfe\xfd")
    with pytest.raises(ValueError, match="Encoding error reading"):
        tabular.read(bad_csv, fmt="csv")


def test_excel_invalid_file_error():
    """Verify ExcelParser catches invalid file structures and raises ValueError."""
    bad_excel = TMP_ROOT / "bad_excel.xlsx"
    bad_excel.write_text(
        "This is definitely not a zip or excel file.", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Failed to load Excel file"):
        tabular.read(bad_excel, fmt="xlsx")


# --- Tests for Parsers using Unified Real Files ---


def test_csv_returns_tables_collection():
    """Verify standard CSV files parse and infer complex types correctly."""
    result = tabular.read(FILE_CSV)

    assert isinstance(
        result, Tables
    ), "CSV parser did not return a Tables object."
    assert len(result.tables) == 1

    table = result.first
    assert table.headers == [
        "ID",
        "Navn",
        "Temp (°C)",
        "US Format",
        "Euro Format",
        "Spaced Format",
        "NBSP Format",
        "Date 1 (dd/mm/yyyy)",
        "Date 2 (dd.mm.yyyy)",
        "Date 3 (yyyy-mm-dd)",
    ]

    assert table.rows[0] == [
        1,
        "Bjørn Ærø",
        25.5,
        1500.5,
        1500.5,
        1500.5,
        1500.5,
        "12/05/2026",
        "12.05.2026",
        "2026-05-12",
    ]
    assert table.rows[1] == [
        2,
        "Tāne Māori",
        -4.0,
        -400.25,
        -400.25,
        -400.25,
        -400.25,
        "14/05/2026",
        "14.05.2026",
        "2026-05-14",
    ]


def test_excel_multi_sheet_and_inference():
    """Verify Excel files return sheets and infer types on complex formats."""
    result = tabular.read(FILE_EXCEL)

    assert isinstance(result, Tables)
    assert len(result.tables) == 2

    sheet_names = [t.name for t in result.tables]
    assert "Mixed Formats" in sheet_names
    assert "Simple Data" in sheet_names

    mixed_table = result.get_table("Mixed Formats")
    assert mixed_table.headers == [
        "ID",
        "Navn",
        "Temp (°C)",
        "US Format",
        "Euro Format",
        "Spaced Format",
        "NBSP Format",
        "Date 1 (dd/mm/yyyy)",
        "Date 2 (dd.mm.yyyy)",
        "Date 3 (yyyy-mm-dd)",
    ]

    assert mixed_table.rows[2] == [
        3,
        "Jörg Müller",
        100.0,
        1000000.0,
        1000000.0,
        1000000.0,
        1000000.0,
        "20/05/2026",
        "20.05.2026",
        "2026-05-20",
    ]

    simple_table = result.get_table("Simple Data")

    assert simple_table.headers == [
        "Project ID",
        "Client",
        "Start Date",
        "Budget (NOK)",
        "Approved",
    ]

    assert simple_table.rows[0] == [
        1001,
        "Trondheim Municipality",
        "27.08.2026",
        8500000,
        True,
    ]
    assert simple_table.rows[1] == [
        1002,
        "Oslo Kommune",
        "15.09.2026",
        12450000,
        False,
    ]


# --- Tests for Table Model Appending, Logging & Features ---


def test_append_table_strict_rejection():
    """Test append_table fails if target lacks source headers and merge=False."""
    t1 = Table("Target", ["A", "B"], [[1, 2]])
    t2 = Table("Source", ["A", "C"], [[3, 4]])

    with pytest.raises(ValueError, match="Unrecognized headers: \\['C'\\]"):
        t1.append_table(t2, merge_headers=False)

    assert len(t1.rows) == 1
    assert t1.headers == ["A", "B"]


def test_append_table_merge_success():
    """Test append_table expands columns and inserts None when merge=True."""
    t1 = Table("Target", ["A", "B"], [[1, 2]])
    t2 = Table("Source", ["A", "C"], [[3, 4]])

    t1.append_table(t2, merge_headers=True)

    assert set(t1.headers) == {"A", "B", "C"}
    assert t1.rows[0] == [1, 2, None]
    assert t1.rows[1] == [3, None, 4]


def test_append_table_logs_error():
    """A mismatch in headers when merging=False logs a specific error."""
    t1 = Table("Target", ["A", "B"], [[1, 2]])
    t2 = Table("Source", ["A", "C"], [[3, 4]])

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)

    logger = logging.getLogger("tabular.models.table")
    old_level = logger.level
    logger.setLevel(logging.ERROR)
    logger.addHandler(handler)

    try:
        with pytest.raises(ValueError):
            t1.append_table(t2, merge_headers=False)

        assert "Unrecognized headers:" in log_capture.getvalue()
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)


def test_csv_parser_sniff_warns_on_fail():
    """Sniffing an empty/invalid file logs a warning gracefully."""
    bad_csv = TMP_ROOT / "empty.csv"
    bad_csv.write_text("", encoding="utf-8")

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)

    logger = logging.getLogger("tabular.parsers.csv_parser")
    old_level = logger.level
    logger.setLevel(logging.WARNING)
    logger.addHandler(handler)

    try:
        tabular.read(bad_csv, sniff_dialect=True)
        assert "Could not sniff dialect" in log_capture.getvalue()
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)


def test_table_indexing_and_iteration():
    """Verify Table supports row/column indexing and iteration."""
    t = Table("Test", ["ID", "Name"], [[1, "Alice"], [2, "Bob"]])

    assert t[0] == [1, "Alice"]
    assert t["Name"] == ["Alice", "Bob"]

    rows = list(t)
    assert len(rows) == 2
    assert rows[1] == [2, "Bob"]

    with pytest.raises(KeyError):
        _ = t["UnknownColumn"]


def test_table_append_from_file_and_write():
    """Verify Table appends data directly from a file and writes to disk."""
    t = Table("Base", ["ID", "Navn", "Temp (°C)"], [[99, "Zero", 0.0]])

    new_data = tabular.read(FILE_CSV)
    t.append_table(new_data.first, merge_headers=True)

    assert len(t.rows) == 4
    assert t.rows[1][:3] == [1, "Bjørn Ærø", 25.5]

    out_path = TMP_ROOT / "table_output.csv"
    tabular.write(t, out_path)
    assert out_path.exists()


def test_table_write_unsupported_format_raises_exception():
    """Verify writing a Table with unregistered format raises ValueError."""
    t = Table("Sheet1", ["A"])

    with pytest.raises(
        ValueError, match="Unsupported format for writing: 'unknownformat'"
    ):
        tabular.write(t, TMP_ROOT / "output.unknownformat")


def test_table_printable():
    """Verify Table has aligned Markdown __str__ and __repr__ representations."""
    t = Table("TestSheet", ["ID", "Name"], [[1, "Alice"], [2, "Bob"]])

    expected_str = (
        "## TestSheet\n"
        "| ID | Name  |\n"
        "|----|-------|\n"
        "| 1  | Alice |\n"
        "| 2  | Bob   |"
    )
    assert str(t) == expected_str
    assert repr(t) == ("<Table(name='TestSheet', columns=2, rows=2)>")


# --- Tests for Tables Model Features ---


def test_tables_init_with_list():
    """Verify Tables initializes directly with a list of Tables."""
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

    ts.remove_table("Sheet2")
    assert len(ts.tables) == 2
    assert ts[1].name == "Sheet3"

    ts.remove_table(0)
    assert len(ts.tables) == 1
    assert ts[0].name == "Sheet3"

    with pytest.raises(TypeError, match="Key must be an integer .* or string"):
        ts.remove_table(cast(Any, {"wrong": "type"}))


def test_tables_indexing_and_iteration():
    """Verify Tables supports indexing by int/name and iteration."""
    t1 = Table("Sheet1", ["A"])
    t2 = Table("Sheet2", ["B"])
    ts = Tables([t1, t2])

    assert ts[0] == t1
    assert ts["Sheet2"] == t2

    table_names = [table.name for table in ts]
    assert table_names == ["Sheet1", "Sheet2"]

    with pytest.raises(KeyError):
        _ = ts["UnknownSheet"]


def test_tables_append_from_file_and_write():
    """Verify Tables appends data from a file and writes to disk dynamically."""
    ts = Tables()
    new_data = tabular.read(FILE_CSV)

    # Append the table from the file
    for table in new_data.tables:
        ts.append_table(table)

    # Add a second dummy table to ensure len(ts.tables) > 1 triggers file splitting
    ts.append_table(Table("second_sheet", ["A"], [[1]]))

    assert len(ts.tables) == 2
    assert ts[0].name == "complex_data"

    split_csv_path = TMP_ROOT / "output.csv"
    tabular.write(ts, split_csv_path)

    # The files should be split using table names
    expected_split_file1 = TMP_ROOT / "output_complex_data.csv"
    expected_split_file2 = TMP_ROOT / "output_second_sheet.csv"

    assert expected_split_file1.exists()
    assert expected_split_file2.exists()


def test_tables_write_unsupported_format_raises_exception():
    """Verify writing a Tables object with unregistered format raises ValueError."""
    ts = Tables([Table("Sheet1", ["A"])])

    with pytest.raises(
        ValueError, match="Unsupported format for writing: 'unknownformat'"
    ):
        tabular.write(ts, TMP_ROOT / "output.unknownformat")


def test_tables_printable():
    """Verify Tables has aligned Markdown __str__ and __repr__ representations."""
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


def test_csv_write_splits_multiple_tables():
    """Verify multi-table collection writing to CSV natively splits files."""
    base_out_csv = TMP_ROOT / "split_output.csv"

    tables = tabular.read(FILE_EXCEL)
    tabular.write(tables, base_out_csv)

    expected_sheet1_path = TMP_ROOT / "split_output_Mixed Formats.csv"
    expected_sheet2_path = TMP_ROOT / "split_output_Simple Data.csv"

    assert (
        expected_sheet1_path.exists()
    ), "CSV splitting failed for Mixed Formats"
    assert (
        expected_sheet2_path.exists()
    ), "CSV splitting failed for Simple Data"

    assert (
        not base_out_csv.exists()
    ), "io.write incorrectly created a merged CSV file instead of splitting."


def test_writers_append_newline():
    """Verify MD and JSON writers append a single newline at file end."""
    t = Table("NewlineTest", ["Col"], [[1]])

    md_path = TMP_ROOT / "test_newline.md"
    json_path = TMP_ROOT / "test_newline.json"

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

    if has_md and md_path.exists():
        md_content = md_path.read_text(encoding="utf-8")
        assert md_content.endswith(
            "\n"
        ), "Markdown generated file must end with a newline character."
        assert not md_content.endswith(
            "\n\n"
        ), "Markdown generated file must have exactly one trailing newline."

    if has_json and json_path.exists():
        json_content = json_path.read_text(encoding="utf-8")
        assert json_content.endswith(
            "\n"
        ), "JSON generated file must end with a newline character."
        assert not json_content.endswith(
            "\n\n"
        ), "JSON generated file must have exactly one trailing newline."


def test_json_unicode_formatting():
    """Verify JSON writer formats unicode natively."""
    tables = tabular.read(FILE_EXCEL)

    json_str = tabular.write(tables, fmt="json")

    assert "Bjørn Ærø" in str(
        json_str
    ), "JSON Writer failed to preserve 'ø' and 'Æ' characters."
    assert "Tāne Māori" in str(
        json_str
    ), "JSON Writer failed to preserve 'ā' and 'ō' characters."
    assert "°C" in str(
        json_str
    ), "JSON Writer failed to preserve the '°' unit symbol."


# --- Standalone Execution Logic ---

if __name__ == "__main__":
    print("Running Tabular Data IO tests standalone...\n")
    test_functions = [
        obj
        for name, obj in globals().items()
        if callable(obj) and name.startswith("test_")
    ]

    PASSED = 0
    FAILED = 0

    for test_func in test_functions:
        sys.stdout.write(f"Running {test_func.__name__} ... ")
        try:
            test_func()
            print("PASSED")
            PASSED += 1
        except (AssertionError, ValueError, TypeError, KeyError, OSError) as e:
            print(f"FAILED\n  -> {type(e).__name__}: {e}")
            FAILED += 1

    print("\n--- Test Run Summary ---")
    print(f"Total: {PASSED + FAILED} | Passed: {PASSED} | Failed: {FAILED}")

    if FAILED > 0:
        raise RuntimeError(f"Test suite failed with {FAILED} errors.")
