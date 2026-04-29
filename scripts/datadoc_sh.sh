mkdir -p output

python scripts/path2dict.py tests/data --csv \
    --config "/@id" \
    --template "@id=physmet:sample/{@id}" \
    --template "@type=chameo:Sample" > output/samples.csv

python scripts/path2dict.py tests/data --csv \
    --config "/sampleId///@id" \
    --template "@id=physmet:dataset/{@id}" \
    --template "processedFrom=physmet:sample/{sampleId}" \
    --template "@type=ddoc:Dataset" > output/datasets.csv

python scripts/path2dict.py tests/data --csv \
    --config "/sampleId/instrument/label/expId" \
    --store_path "localPath" \
    --template "hasInput=physmet:sample/{sampleId}" \
    --template "hasOutput=physmet:dataset/{expId}" \
    --template "@id=physmet:procedure/{localPath}" \
    --template "@type=ddoc:Procedure" > output/procedures.csv
