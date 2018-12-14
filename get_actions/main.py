from flask import Flask, jsonify, request, abort
from elasticsearch import Elasticsearch
import math

app = Flask(__name__)


client = Elasticsearch([{'host': 'api3.eostribe.io', 'port': '9200'}])

@app.route('/v2/history/get_actions', methods=['POST'])
def get_actions():

    pos = request.get_json(force=True).get('pos')

    offset = request.get_json(force=True).get('offset')

    account_name =request.get_json(force=True).get('account_name')

    if not isinstance(pos, int) or not isinstance(offset, int):
        return abort(404)
    elif pos == -1 and offset == -1:
        seeking_result = seeking_actions(0, 1, account_name)
    elif pos <= -1 and (1 <= math.fabs(offset) <= 1000):
        pos = int( math.fabs(pos))+1
        seeking_result = seeking_actions(pos , int( math.fabs(offset)), account_name)
    else:
        return abort(404)
        #seeking_result = seeking_actions(pos, offset, account_name)

    if seeking_result is None:
        return abort(404)

    return jsonify(seeking_result)

def seeking_actions(pos, offset, account_name):
    resp = client.search(index='action_traces', filter_path=['hits.hits._*'],
                         size=offset, from_=pos,
                         body={
                             "query":
                                 {"match":
                                      {"act.account": account_name
                                       }
                                  },
                             "sort": [
                                 {"block_num": {"order": "desc"}}
                             ]
                         })
    if len(resp) == 0:
        return None

    result = []

    for field in resp['hits']['hits']:
        result.append(field['_source'])

    return {"actions":result}




if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500, debug=True)