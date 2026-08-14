#!/bin/bash

# Enter repository root directory
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"/..

# Generate JSON-LD file with custom prefixes
python src/scripts/extract_prefixes.py templates -o schema/prefixes.json

# Don't crash pre-commit in case the above fails on GitHub
exit 0
