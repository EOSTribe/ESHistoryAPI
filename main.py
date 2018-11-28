from flask import Flask, jsonify, request
import json
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from flask import Response





app = Flask(__name__)

client = Elasticsearch([{'host': '10.0.64.25', 'port': '9200'}])


@app.route('/v1/history/get_transaction', methods=['POST'])
def get_transaction():
    request_transaction = request.get_json().get('id')
    return jsonify(req_transaction(request_transaction))


def dsl_req_transaction(req_transaction_id):
    s = Search(using=client, index="transaction_traces")\
        .query("match", id=req_transaction_id)
    s = s.source(['producer_block_id', 'net_usage', 'id', 'except', 'elasped','createAt','block_time', 'block_num','action_traces'])
    response = s.execute()
    res=[]
    for hit in response:
        res.append(hit['producer_block_id'])
        res.append(hit['net_usage'])
        res.append(hit['action_traces'])
    return json.JSONEncoder().encode(res)


def req_transaction(trx_id):
    resp = client.search(index='action_traces', body={
        "query":
            {"match":
                 {"trx_id": trx_id
            }
        }
    })

    res=[]

    for hit in resp['hits']['hits']:
        for result in hit['_source']:
            res.append(hit['_source'][result])
    return res

    #return resp['hits']['hits'][0]['_source']
    #return tmp_resp['_source']


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5500, debug=True)