from flask import Flask, jsonify, request, abort
from elasticsearch import Elasticsearch

app = Flask(__name__)


client = Elasticsearch([{'host': 'api3.eostribe.io', 'port': '9200'}])


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
    print("Found %d messages" % resp['hits']['total'])

    if int(resp['hits']['total']) == 0:
        return None

    for field in resp['hits']['hits']:
        print("Sender: %s\n    Subject: %s" % (field['_source']['block_num'], field['_source']['id']))
        result = {'id':field['_source']['id'],
                   'receipt': field['_source']['receipt'],
                              #'cpu_usage_us':field['_source']['receipt.cpu_usage_us'],
                              #'net_usage_words': field['_source']['receipt.net_usage_words']
                  'producer_block_id': field['_source']['producer_block_id'],
                  'action_traces': field['_source']['action_traces'],
                  'block_num': field['_source']['block_num'],
                  'block_time': field['_source']['block_time'],
                  'createAt': field['_source']['createAt'],
                  'elapsed': field['_source']['elapsed'],
                  'net_usage': field['_source']['net_usage'],
        }



    return result



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5500, debug=True)