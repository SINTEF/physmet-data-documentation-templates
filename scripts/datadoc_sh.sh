python scripts/path2dict.py tests/data --config "/identifier" --csv > sample.csv.temp
python scripts/path2dict.py tests/data --config "/processedFrom.identifier///identifier" --csv > dataset.csv.temp
python scripts/path2dict.py tests/data --config "/hasInput.identifier/instrument/@type.identifier/hasOutput.identifier" --csv > process.csv.temp
