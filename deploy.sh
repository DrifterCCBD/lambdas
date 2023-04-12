#!/bin/bash

find . -name "*.py" | while read fn_path; do
	fn="$(printf "$fn_path" | sed 's+.*/++' | sed 's/\.py//')"
	cp $fn_path lambda_function.py;
	zip "${fn}.zip" lambda_function.py;
	aws lambda update-function-code \
	--function-name "${fn}" \
	--zip-file "fileb://${fn}.zip";
	rm "${fn}.zip"
done
rm lambda_function.py
