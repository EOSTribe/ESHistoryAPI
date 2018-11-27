from flask import Flask, jsonify, request
from elasticsearch import Elasticsearch




app = Flask(__name__)


@app.route('/v1/history/get_transaction', methods=['POST'])
def get_transaction():
    request_transaction = request.get_json().get('id')
    return jsonify(req_transaction(request_transaction))

def req_transaction(trx_id):
    es= Elasticsearch([{'host': '10.0.64.25', 'port': '9200'}])
    resp = es.search(index='transaction_traces', body={
        "query":
            {"match":
                 {"id": trx_id
            }
        }
    })
    tmp_resp = resp['hits']['hits'][0]['_source']
    return tmp_resp['_source']


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5500, debug=True)