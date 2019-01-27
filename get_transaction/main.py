from flask import Flask, Response, request, abort
from elasticsearch import Elasticsearch
import os
import json


app = Flask(__name__)

ELASTIC_HOST = os.environ['ELASTIC_HOST']
ELASTIC_PORT = os.environ['ELASTIC_PORT']

client = Elasticsearch([{'host': ELASTIC_HOST, 'port': ELASTIC_PORT}], timeout=30)

@app.route('/v1/history/get_transaction', methods=['POST'])
@app.route('/v2/history/get_transaction', methods=['POST'])
def get_transaction():
    if request.headers['X-Forwarded-Host'] == 'api.worbli.eostribe.io':
        elasticIndex = "worbli_transaction_traces*"
    elif request.headers['X-Forwarded-Host'] == 'api.bos.eostribe.io':
        elasticIndex = "bos_transaction_traces*"
    elif request.headers['X-Forwarded-Host'] == 'api.telos.eostribe.io':
        elasticIndex = "telos_transaction_traces*"
    else:
        elasticIndex = "transaction_traces*"

    transaction_id = request.get_json(force=True).get('id')

    if len(transaction_id) != 64:
        return abort(404)

    seeking_result = seeking_transaction(transaction_id, elasticIndex)

    if seeking_result is None:
        return abort(404)

    json_string = json.dumps(seeking_result, ensure_ascii=False)
    response = Response(json_string, content_type="application/json; charset=utf-8")
    return response

def seeking_transaction(transaction_id, es_index):
    resp = client.search(index=es_index, filter_path=['hits.hits._*'],
     body={
        "query":
            {"match":
                 {"id": transaction_id
            }
        }
    })

    if len(resp) == 0:
        return None

    result = []

    for field in resp['hits']['hits']:
        result.append(field['_source'])
    return result

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500, debug=True)
    app.config['JSON_AS_ASCII'] = False
