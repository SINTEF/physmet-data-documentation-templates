import subprocess

def test_path2dict_cli():
    result = subprocess.run(
        ["python", "scripts/path2dict.py", "tests/data", "--config", "/sample/instrument/method/experiment"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "JO11" in result.stdout
    assert """sample="JM12" / instrument="SEM" / method="EDS" / experiment="220304f" /""" in result.stdout
    return result.stdout

if __name__ == "__main__":
    result = test_path2dict_cli()
    print(result)
