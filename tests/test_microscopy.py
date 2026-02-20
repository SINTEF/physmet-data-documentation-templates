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
    
    # Verify that the project readme.txt was created
    project_readme = output_dir / "PhysMet" / "readme.txt"
    assert project_readme.exists(), f"Project readme.txt not created: {project_readme}"
    
    # Verify readme contains project info
    readme_content = project_readme.read_text(encoding='utf-8')
    assert "PhysMet" in readme_content, "Project name not in readme.txt"
    assert "PROJECT DOCUMENTATION" in readme_content, "Template header not in readme.txt"
    
    # Verify that instruments.csv and processing.csv were created
    instruments_csv = output_dir / "PhysMet" / "instruments.csv"
    assert instruments_csv.exists(), f"instruments.csv not created: {instruments_csv}"
    
    processing_csv = output_dir / "PhysMet" / "processing.csv"
    assert processing_csv.exists(), f"processing.csv not created: {processing_csv}"


def test_add_sample():
    """Test the command line for adding a SEM characterization session.

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

    # Manually add a sample to samples.csv (as users would do)
    samples_file = output_dir / "TestProject" / "samples.csv"
    with open(samples_file, 'a', encoding='utf-8') as f:
        f.write('SAMPLE001, 2026-02-20, [P001]\n')

    # Then, add a SEM characterization session for that sample
    cmd_add = [sys.executable, str(script), "add", "-s", "SAMPLE001", "-d", "2026-02-20", "-p", "TestProject"]

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
    
    # Verify that the SEM folder and readme.txt were created
    sem_folder = output_dir / "TestProject" / "SEM" / "SEM_SAMPLE001_2026-02-20"
    assert sem_folder.exists(), f"SEM folder not created: {sem_folder}"
    
    readme_file = sem_folder / "readme.txt"
    assert readme_file.exists(), f"readme.txt not created: {readme_file}"
    
    # Verify readme contains sample info
    readme_content = readme_file.read_text(encoding='utf-8')
    assert "SAMPLE001" in readme_content, "Sample ID not in readme.txt"
    assert "2026-02-20" in readme_content, "Date not in readme.txt"


if __name__ == "__main__":

    clean_output_folder()

    test_create_folder()
    
    test_add_sample()