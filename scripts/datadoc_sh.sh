mkdir -p output

python scripts/path2dict.py tests/data --config "/@id" --csv \
    --template "@id=physmet:sample/{value}" |
    csvsql --query "SELECT *, 'chameo:Sample' AS \"@type\" FROM stdin" > output/samples.csv

python scripts/path2dict.py tests/data --config "/processedFrom///@id" --csv \
    --template "@id=physmet:dataset/{value}" \
    --template "processedFrom=physmet:sample/{value}" |
    csvsql --query "SELECT *, 'ddoc:Dataset' AS \"@type\" FROM stdin" > output/datasets.csv

python scripts/path2dict.py tests/data --config "/hasInput/instrument/label/hasOutput" --csv \
    --store_path "localPath" \
    --template "hasInput=physmet:sample/{value}" \
    --template "hasOutput=physmet:dataset/{value}" |
    csvsql --query "SELECT *, 'ddoc:Procedure' AS \"@type\" FROM stdin" |
    csvsql --query "SELECT *, 'physmet:procedure/' || \"localPath\" AS \"@id\" FROM stdin" > output/procedures.csv
