from flask import Flask, jsonify, request, abort, Response
from elasticsearch import Elasticsearch
import math
import os

app = Flask(__name__)

ELASTIC_HOST = os.environ['ELASTIC_HOST']
ELASTIC_PORT = os.environ['ELASTIC_PORT']

client = Elasticsearch([{'host': ELASTIC_HOST, 'port': ELASTIC_PORT}], timeout=30)

@app.route('/v2/history/get_actions', methods=['POST'])
def get_actions():

    pos = request.get_json(force=True).get('pos')

    offset = request.get_json(force=True).get('offset')

    account_name =request.get_json(force=True).get('account_name')

    if isinstance(account_name, str) and ( pos == None and offset == None):
        seeking_result = seeking_actions(account_name)
    elif not isinstance(pos, int) or not isinstance(offset, int):
        return abort(404)
    else:
         seeking_result = seeking_actions(pos, offset, account_name)

    if seeking_result is None:
        return abort(404)

    return jsonify(seeking_result)

def seeking_actions(pos, offset, account_name):

    if pos == -1 and offset == -1:
        pos = 0
        offset = 1
        sortOrder = 'desc'

    elif pos <= -1 and  offset <= 0 :
        pos = int( math.fabs(pos))-1
        offset = int( math.fabs(offset))
        sortOrder = 'desc'
    elif 0 <= pos and 0 <= offset:
        sortOrder = 'asc'
    else: return None



    resp = client.search(index='action_traces', filter_path=['hits.hits._*'],
                         size=offset, from_=pos,
                         body={
                             "query":
                                 {"match":
                                      {"act.account": account_name
                                       }
                                  },
                             "sort": [
                                 {"_id": {"order": sortOrder}}
                             ],
                             "timeout": '10s'
                         })
    if len(resp) == 0:
        return None

    result = []

    for field in resp['hits']['hits']:
        result.append(field['_source'])

    return {"actions":result}

def seeking_actions(account_name):
    resp = client.search(index='new_action_traces', filter_path=['hits.hits._*'],
                         body={
                             "query":
                                 {"multi_match":
                                     {
                                         "query": account_name,
                                         "fields": ["act.account", "act.data", "receipt.receiver"]
                                     }
                                },
                             "sort": [
                                 {"_id": {"order": "desc"}}
                             ],
                             "timeout": '10s'
                         })
    if len(resp) == 0:
        return None

    result = []

    for field in resp['hits']['hits']:
        result.append(field['_source'])

    return {"actions":result}




if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500, debug=True)
    app.config['JSON_AS_ASCII'] = False
