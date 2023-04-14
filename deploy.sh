#!/bin/bash

POSTGRES_HOSTNAME="database-1.cgwwmxrgggyq.us-east-1.rds.amazonaws.com"
POSTGRES_PORT="5432"
POSTGRES_DB="postgres"


test -e package && rm -r package
mkdir -p package
pip3 install --target package psycopg2-binary >/dev/null 2>/dev/null
wget https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem -O package/global-bundle.pem
( 
	cd package
	zip -r ../package.zip . >/dev/null 2>/dev/null
)
aws lambda publish-layer-version --layer-name postgres-lib \
    --description "Postgres Library" \
    --license-info "MIT" \
    --zip-file fileb://package.zip \
    --compatible-runtimes python3.8 python3.9 \
    --compatible-architectures "x86_64" | tee -a layer_log
cat layer_log | jq  --raw-output ".LayerVersionArn"

rm -r package package.zip 

find . -path ./package -prune -o -name "*.py" | while read fn_path; do
	fn="$(printf "$fn_path" | sed 's+.*/++' | sed 's/\.py//')"
	cp $fn_path lambda_function.py;
	zip "${fn}.zip" lambda_function.py;
	aws lambda update-function-code \
	--function-name "${fn}" \
	--zip-file "fileb://${fn}.zip";
	rm "${fn}.zip"
done
rm lambda_function.py

find . -path ./package -prune -o -name "*.py" | while read fn_path; do
	fn="$(printf "$fn_path" | sed 's+.*/++' | sed 's/\.py//')"
	aws lambda update-function-configuration \
			--function-name "${fn}" \
			--layers "$(cat layer_log | jq ".LayerVersionArn")" \
			--environment "{\"Variables\":{\"POSTGRES_HOSTNAME\":\"${POSTGRES_HOSTNAME}\",\"POSTGRES_PORT\":\"${POSTGRES_PORT}\",\"POSTGRES_DB\":\"${POSTGRES_DB}\",\"POSTGRES_USER\":\"${POSTGRES_USER}\",\"POSTGRES_PASS\":\"${POSTGRES_PASS}\"}}"
done
