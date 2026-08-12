mkdir -p output

python scripts/path2dict.py tests/data --intent "sample" --csv > output/samples.csv
python scripts/path2dict.py tests/data --intent "dataset" --csv > output/datasets.csv
python scripts/path2dict.py tests/data --intent "procedure" --csv > output/procedures.csv
