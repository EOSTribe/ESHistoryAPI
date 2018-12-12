from flask import Flask, jsonify, request, abort, Response
from elasticsearch import Elasticsearch
import math
import os

app = Flask(__name__)

ELASTIC_HOST = os.environ['ELASTIC_HOST']
ELASTIC_PORT = os.environ['ELASTIC_PORT']

client = Elasticsearch([{'host': 'api3.eostribe.io', 'port': '9200'}])

@app.route('/v1/history/get_actions', methods=['POST'])
def get_actions():

    pos = request.get_json(force=True).get('pos')

    offset = request.get_json(force=True).get('offset')

    account_name =request.get_json(force=True).get('account_name')

    if not isinstance(pos, int) or not isinstance(offset, int):
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
    elif 0 <= pos and 0 < offset:
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
                             "timeout": '6s'
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
