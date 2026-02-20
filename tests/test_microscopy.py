
""" Functions to test the microscopy tools. """

import subprocess
import sys
from pathlib import Path
import shutil
import stat

output_dir = Path(__file__).resolve().parent / "output"


def clean_output_folder():
    """Remove all files and folders inside the tests/output directory.

    The function leaves the `output` directory itself in place; it only
    removes its children.
    """
    if not output_dir.exists():
        return

    for child in output_dir.iterdir():
        try:
            if child.is_dir():
                shutil.rmtree(child)
            else:
                # ensure writable before unlinking (Windows readonly files)
                try:
                    child.unlink()
                except PermissionError:
                    child.chmod(child.stat().st_mode | stat.S_IWRITE)
                    child.unlink()
        except Exception:
            # propagate with context for caller to handle
            raise


def run_script(args: list, input_data: str = None):
    """ Run a command "$ python physmet-folders.py ARGS" with user inputs """

    output_dir.mkdir(exist_ok=True)

    # locate the script relative to the repository root
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "microscopy/scripts/physmet-folders.py"

    cmd = [sys.executable, str(script)] + args

    proc = subprocess.run(
        cmd,
        cwd=output_dir,
        capture_output=True,
        text=True,
        input=input_data,
        timeout=30,
    )
    return proc


def process_str(proc, msg):
    s = f"{msg} (rc={proc.returncode})\n"
    s += f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    return s


def test_create_folder():
    """Test the command line for the creation of the folder.

    This runs `python physmet-folders.py init` with the working directory
    set to the `tests/output` folder.
    """

    # inputs: accept defaults for project name, author, and directory
    input_data = "\n\n\n"
    # run script
    proc = run_script(["init", "-p", "PhysMet"], input_data)

    assert proc.returncode == 0, process_str(proc, 'Command failed')

    # Verify that the project readme.txt was created
    path = output_dir / "PhysMet" / "readme.txt"
    assert path.exists(), f"{path.name} not created: {path}"

    # Verify readme contains project info
    readme_content = path.read_text(encoding='utf-8')
    assert "PhysMet" in readme_content, "Project name not in readme.txt"
    doc = "PROJECT DOCUMENTATION"
    assert doc in readme_content, "Template header not in readme.txt"

    # Verify that instruments.csv and processing.csv were created
    path = output_dir / "PhysMet" / "instruments.csv"
    assert path.exists(), f"{path.name} not created: {path}"

    path = output_dir / "PhysMet" / "processing.csv"
    assert path.exists(), f"{path.name} not created: {path}"


def test_add_sample():
    """Test the command line for adding a sample to a project.

    This runs `python physmet-folders.py add -s SAMPLE_ID -d YYYY-MM-DD`
    with the working directory set to the `tests/output` folder.
    """
    # inputs: accept defaults for project name, author, and directory
    input_data = "\n\n\n"
    # run script to create a project
    init = run_script(["init", "-p", "TestProject"], input_data)

    assert init.returncode == 0, process_str(init, 'Init command failed')

    # run script to add sample
    add = run_script([
        "add", "-s", "SAMPLE001", "-d", "2026-02-20", "-p", "TestProject"
    ])

    assert add.returncode == 0, process_str(add, 'Add command failed')

    # Verify that the SEM folder and readme.txt were created
    sem = output_dir / "TestProject" / "SEM" / "SEM_SAMPLE001_2026-02-20"
    assert sem.exists(), f"{sem.name} not created: {sem}"

    path = sem / "readme.txt"
    assert path.exists(), f"{path.name} not created: {path}"

    # Verify readme contains sample info
    readme_content = path.read_text(encoding='utf-8')
    assert "SAMPLE001" in readme_content, "Sample ID not in readme.txt"
    assert "2026-02-20" in readme_content, "Date not in readme.txt"


if __name__ == "__main__":

    clean_output_folder()

    test_create_folder()

    test_add_sample()
