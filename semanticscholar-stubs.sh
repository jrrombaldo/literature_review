curl -s -H "Content-type: application/json" \
-X POST -d '{"options": {"packageName": "semanticscholar"},"swaggerUrl": "https://api.semanticscholar.org/graph/v1/swagger.json"}' \
https://generator.swagger.io/api/gen/clients/python \
| jq -r ".link" \
| xargs -I {} wget {} -O client.zip \
&& pip install client.zip \
&& rm -rf client.zip


# wget https://api.semanticscholar.org/graph/v1/swagger.json -O swagger.json

# swagger_style.py --swagger_path ./swagger.json --with_line_number

# swagger_to_py_client.py  --swagger_path ./swagger.json --outpath ./semantic.py



