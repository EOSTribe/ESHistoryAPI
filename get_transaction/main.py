from flask import Flask, Response, request, abort
from elasticsearch import Elasticsearch
import os
import json
from flask_cors import CORS, cross_origin


app = Flask(__name__)
CORS(app)

ELASTIC_HOST = os.environ['ELASTIC_HOST']
ELASTIC_PORT = os.environ['ELASTIC_PORT']

client = Elasticsearch([{'host': ELASTIC_HOST, 'port': ELASTIC_PORT}], timeout=30)

@app.route('/v1/history/get_transaction', methods=['POST','OPTIONS','GET'])
@app.route('/v2/history/get_transaction', methods=['POST','OPTIONS','GET'])
@cross_origin()
def get_transaction():
    if request.headers['X-Forwarded-Host'] == 'api.worbli.eostribe.io':
        elasticIndex = "worbli_transaction_traces*"
    elif request.headers['X-Forwarded-Host'] == 'api.bos.eostribe.io':
        elasticIndex = "bos_transaction_traces*"
    elif request.headers['X-Forwarded-Host'] == 'api.telos.eostribe.io':
        elasticIndex = "telos_transaction_traces*"
    elif request.headers['X-Forwarded-Host'] == 'api.meetone.eostribe.io':
        elasticIndex = "meetone_transaction_traces*"
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
    # response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS,GET')
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

    for field in resp['hits']['hits']:
        field['_source']['trx'] = {}
        field['_source']['trx']['receipt'] = field['_source']['receipt']
        return field['_source']

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500, debug=True)
    app.config['JSON_AS_ASCII'] = False
