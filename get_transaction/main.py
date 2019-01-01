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

    transaction_id = request.get_json(force=True).get('id')

    if len(transaction_id) != 64:
        return abort(404)

    seeking_result = seeking_transaction(transaction_id)

    if seeking_result is None:
        return abort(404)

    json_string = json.dumps(seeking_result, ensure_ascii=False)
    response = Response(json_string, content_type="application/json; charset=utf-8")
    return response

def seeking_transaction(transaction_id):
    resp = client.search(index='transaction_traces', body={
        "query":
            {"match":
                 {"id": transaction_id
            }
        }
    })

    if int(resp['hits']['total']) == 0:
        return None

    for field in resp['hits']['hits']:
        result = {'id':field['_source']['id'],
                  'receipt': field['_source']['receipt'],
                  'producer_block_id': field['_source']['producer_block_id'],
                  'action_traces': field['_source']['action_traces'],
                  'block_num': field['_source']['block_num'],
                  'block_time': field['_source']['block_time'],
                  'createAt': field['_source']['createAt'],
                  'elapsed': field['_source']['elapsed'],
                  'net_usage': field['_source']['net_usage']
        }
        return result

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500, debug=True)
    app.config['JSON_AS_ASCII'] = False
