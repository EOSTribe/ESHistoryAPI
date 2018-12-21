from flask import Flask, jsonify, request, abort, Response
from elasticsearch import Elasticsearch
import math
import json
import os

app = Flask(__name__)

ELASTIC_HOST = os.environ['ELASTIC_HOST']
ELASTIC_PORT = os.environ['ELASTIC_PORT']

client = Elasticsearch([{'host': ELASTIC_HOST, 'port': ELASTIC_PORT}], timeout=30)

@app.route('/v2/history/get_key_accounts', methods=['POST'])
def get_key_accounts():

    public_key = request.get_json(force=True).get('public_key')


    if isinstance(public_key, str) and public_key != None:
        seeking_result = seeking_actions(public_key)
    else:
        return abort(404)

    if seeking_result is None:
        return abort(404)

    json_string = json.dumps(seeking_result,ensure_ascii = False)
    response = Response(json_string, content_type="application/json; charset=utf-8")
    return response

def seeking_actions(public_key):
    resp = client.search(index='accounts', filter_path=['hits.hits._*'],
                         body={
                             "query":
                                 {"match":
                                      {"pub_keys.key": public_key
                                       }
                                  }
                         })
    if len(resp) == 0:
        return None

    result = []

    for field in resp['hits']['hits']:
        result.append(field['_source']['name'])

    return {"account_names":result}


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500, debug=True)
    app.config['JSON_AS_ASCII'] = False
