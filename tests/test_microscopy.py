"""Functions to test the microscopy tools."""

from pathlib import Path
import shutil
import stat


def clean_output_folder():
    """Remove all files and folders inside the tests/output directory.

    The function leaves the `output` directory itself in place; it only
    removes its children.
    """
    output_dir = Path(__file__).parent / "output"
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


# create a project folder (run the command and answer the questions):
#      $ python physmet-folders.py init
def test_create_folder():
    """Test the command line for the creation of the folder.

    This runs `python physmet-folders.py init` with the working directory
    set to the `tests/output` folder.
    """
    import subprocess
    import sys

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    # locate the script relative to the repository root
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "microscopy" / "scripts" / "physmet-folders.py"

    cmd = [sys.executable, str(script), "init", "-p", "PhysMet"]

    # Provide input to accept default values for:
    # 1. Project/Folder name (defaults to "PhysMet" from -p arg)
    # 2. Author name
    # 3. Destination directory
    input_data = "\n\n\n"

    proc = subprocess.run(
        cmd,
        cwd=output_dir,
        capture_output=True,
        text=True,
        input=input_data,
        timeout=30,
    )

    assert proc.returncode == 0, (
        f"Command failed (rc={proc.returncode})\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )


def test_add_sample():
    """Test the command line for adding a sample to a project.

    This runs `python physmet-folders.py add -s SAMPLE_ID -d YYYY-MM-DD`
    with the working directory set to the `tests/output` folder.
    """
    import subprocess
    import sys

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    # locate the script relative to the repository root
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "microscopy" / "scripts" / "physmet-folders.py"

    # First, create a project
    cmd_init = [sys.executable, str(script), "init", "-p", "TestProject"]
    input_data = "\n\n\n"  # Accept defaults for project name, author, and directory

    proc_init = subprocess.run(
        cmd_init,
        cwd=output_dir,
        capture_output=True,
        text=True,
        input=input_data,
        timeout=30,
    )

    assert proc_init.returncode == 0, (
        f"Init command failed (rc={proc_init.returncode})\nstdout:\n{proc_init.stdout}\nstderr:\n{proc_init.stderr}"
    )

    # Then, add a sample
    cmd_add = [sys.executable, str(script), "add", "-s", "SAMPLE_001", "-d", "2026-02-20", "-p", "TestProject"]

    proc_add = subprocess.run(
        cmd_add,
        cwd=output_dir,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc_add.returncode == 0, (
        f"Add command failed (rc={proc_add.returncode})\nstdout:\n{proc_add.stdout}\nstderr:\n{proc_add.stderr}"
    )


if __name__ == "__main__":

    clean_output_folder()

    test_create_folder()
    
    test_add_sample()