from flask import Flask, jsonify, request, abort, Response
from elasticsearch import Elasticsearch
import math
import json
import os

app = Flask(__name__)

ELASTIC_HOST = os.environ['ELASTIC_HOST']
ELASTIC_PORT = os.environ['ELASTIC_PORT']
client = Elasticsearch([{'host': ELASTIC_HOST, 'port': ELASTIC_PORT}], timeout=30)

@app.route('/v1/history/find_actions', methods=['POST'])
@app.route('/v2/history/find_actions', methods=['POST'])
def get_key_accounts():
    if request.headers['X-Forwarded-Host'] == 'api.worbli.eostribe.io':
        elasticIndex = "worbli_action_traces*"
    elif request.headers['X-Forwarded-Host'] == 'api.bos.eostribe.io':
        elasticIndex = "bos_action_traces*"
    elif request.headers['X-Forwarded-Host'] == 'api.telos.eostribe.io':
        elasticIndex = "telos_action_traces*"
    else:
        elasticIndex = "action_traces*"

    data = request.get_json(force=True).get('data')


    if isinstance(data, str) and data != None:
        seeking_result = seeking_actions(data, elasticIndex)
    else:
        return abort(404)

    if seeking_result is None:
        return abort(404)

    json_string = json.dumps(seeking_result,ensure_ascii = False)
    response = Response(json_string, content_type="application/json; charset=utf-8")
    return response

def seeking_actions(data, es_index):
    resp = client.search(index=es_index, filter_path=['hits.hits._*'],
                         body={"query":
                                   {"bool": {"filter": [
                                       {"bool":
                                           {"should": [
                                               {"match_phrase":
                                                    {"act.data": data}}],
                                       "minimum_should_match": 1}}]}},
                             "timeout": '10s'}
                         )
    if len(resp) == 0:
        return None

    result = []

    for field in resp['hits']['hits']:
        result.append(field['_source'])

    return {"actions":result}


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500, debug=True)
    app.config['JSON_AS_ASCII'] = False
