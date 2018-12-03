from flask import Flask, jsonify, request, abort
from elasticsearch import Elasticsearch

app = Flask(__name__)


client = Elasticsearch([{'host': '10.0.64.25', 'port': '9200'}])

@app.route('/v1/history/get_transaction', methods=['POST'])
def get_transaction():

    transaction_id = request.get_json(force=True).get('id')

    if len(transaction_id) != 64:
        return abort(404)

    seeking_result = seeking_transaction(transaction_id)

    if seeking_result == None:
        return abort(404)

    return jsonify(seeking_result)

def seeking_transaction(transaction_id):
    resp = client.search(index='transaction_traces', body={
        "query":
            {"match":
                 {"id": transaction_id
            }
        }
    })
    # print("Found %d messages" % resp['hits']['total'])

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
                  'net_usage': field['_source']['net_usage'],
        }

    return result

@app.route('/v1/history/get_actions', methods=['POST'])
def get_actions():

    pos = request.get_json(force=True).get('pos')

    offset = request.get_json(force=True).get('offset')

    account_name =request.get_json(force=True).get('account_name')

    if not isinstance(pos, int) or not isinstance(offset, int):
        return abort(404)

    seeking_result = seeking_actions(pos, offset, account_name)

    if seeking_result == None:
        return abort(404)

    return jsonify(seeking_result)




def seeking_actions(pos, offset, account_name):
    resp = client.search(index='action_traces', filter_path=['hits.hits._*'],
                         size=offset, from_=pos,
                         body={
                             "query":
                                 {"match":
                                      {"act.name": account_name
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

    return result




if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500, debug=True)