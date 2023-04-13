#!/bin/bash

POSTGRES_HOSTNAME="database-1.cgwwmxrgggyq.us-east-1.rds.amazonaws.com"
POSTGRES_PORT="5432"
POSTGRES_DB="postgres"

git log
test -e package && rm -r package
mkdir -p package
pip3 install --target package py-postgresql
wget https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem -O package/global-bundle.pem
find . -name "*.py" | while read fn_path; do
	fn="$(printf "$fn_path" | sed 's+.*/++' | sed 's/\.py//')"
	cp $fn_path lambda_function.py;
	( 
		cd package
		zip -r ../${fn}.zip .
	)
	zip "${fn}.zip" lambda_function.py;
	aws lambda update-function-code \
	--function-name "${fn}" \
	--zip-file "fileb://${fn}.zip";
	rm "${fn}.zip"
	aws lambda update-function-configuration \
		--function-name "${fn}" \
		--environment "{\"POSTGRES_HOSTNAME\"=\"${POSTGRES_HOSTNAME}\",\"POSTGRES_PORT\"=\"${POSTGRES_PORT}\",\"POSTGRES_DB\"=\"${POSTGRES_DB}\",\"POSTGRES_USER\"=\"${POSTGRES_USER}\",POSTGRES_PASS=\"${POSTGRES_PASS}\""
done
rm lambda_function.py
