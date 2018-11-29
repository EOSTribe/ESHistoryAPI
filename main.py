from flask import Flask, jsonify, request
from elasticsearch import Elasticsearch

app = Flask(__name__)


client = Elasticsearch([{'host': 'api3.eostribe.io', 'port': '9200'}])


@app.route('/v1/history/get_transaction', methods=['POST'])
def get_transaction():
    request_transaction = request.get_json().get('id')
    return jsonify(req_transaction(request_transaction))


def req_transaction(transaction_id):
    resp = client.search(index='transaction_traces', body={
        "query":
            {"match":
                 {"id": transaction_id
            }
        }
    })
    print("Found %d messages" % resp['hits']['total'])
    #receipt":{"status":"executed","cpu_usage_us":705,"net_usage_words":38},

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
        }



    #response = resp['hits']['hits']


    return result
    #for hit in resp['hits']['hits']:
     #   for result in hit['_source']:
     #       res.append(hit['_source'][result])
    #return res

    #return resp['hits']['hits'][0]['_source']
    #return tmp_resp['_source']


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5500, debug=True)