import datetime
from flask import Flask, jsonify, request, abort, Response
from elasticsearch import Elasticsearch
import math
import json
import os

app = Flask(__name__)

ELASTIC_HOST = os.environ['ELASTIC_HOST']
ELASTIC_PORT = os.environ['ELASTIC_PORT']
client = Elasticsearch([{'host': ELASTIC_HOST, 'port': ELASTIC_PORT}], timeout=30)


@app.route('/v1/history/get_actions', methods=['POST'])
@app.route('/v2/history/get_actions', methods=['POST'])
def get_actions():

    pos = request.get_json(force=True).get('pos')

    offset = request.get_json(force=True).get('offset')

    account_name =request.get_json(force=True).get('account_name')

    last_days = request.get_json(force=True).get('last_days')

    from_date =  request.get_json(force=True).get('from_date')

    to_date =  request.get_json(force=True).get('to_date')

    if account_name == None:
        return 404
    elif last_days != None:
        seeking_result = seeking_actions_last_days(account_name, str(last_days))
    elif from_date != None and to_date != None:
        seeking_result = seeking_actions_to_from(account_name,from_date,to_date)
    elif not isinstance(pos, int) or not isinstance(offset, int):
        return abort(404)
    elif pos == None and offset == None and last_days == None and from_date == None and to_date== None:
        seeking_result = seeking_actions_account_name(account_name)
    else:
         seeking_result = seeking_actions(account_name,pos = pos, offset = offset )
    if seeking_result is None:
        return abort(404)

    json_string = json.dumps(seeking_result,ensure_ascii = False)
    response = Response(json_string, content_type="application/json; charset=utf-8")
    return response


def seeking_actions_account_name(account_name):
    resp = client.search(index='action_traces', filter_path=['hits.hits._*'],
         body={"query":
                    {"multi_match":
                      {
                      "query": account_name,
                      "fields": ["act.account", "receipt.receiver", "act.data"]
                      }
                    },
                    "sort": [
                      {"block_time": {"order": "desc"}}
                      ],
                    "timeout": '20s'
                    }
                )

    if len(resp) == 0:
        return None

    result = []

    for field in resp['hits']['hits']:
        result.append(field['_source'])

    return {"actions": result}

def seeking_actions_last_days(account_name, last_days):
    resp = client.search(index='action_traces', filter_path=['hits.hits._*'], size = 10000,
                         body={
                             "query": {
                                 "bool": {
                                     "must": [
                                         {"multi_match":
                                              {"query": account_name,
                                               "fields": ["act.account", "receipt.receiver", "act.data"]
                                               }}],
                                     "filter": [
                                         {"range": {"block_time": {"gte": "now-"+last_days+"d/d", "lt": "now/d"}}}
                                     ]
                                 }},
                             "timeout": '20s'
                         }
                         )

    if len(resp) == 0:
        return None

    result = []

    for field in resp['hits']['hits']:
        result.append(field['_source'])

    return {"actions": result}

def seeking_actions(account_name, **kwargs):
    if kwargs.get('pos') == None:
        pos = None
        offset = None
    else:
        pos = kwargs.get('pos')
        offset = kwargs.get('offset')

    if pos == None and offset == None:
        sortOrder = 'desc'
        pos = 0
        offset = 10
    elif pos == -1 and offset == -1:
        pos = 0
        offset = 1
        sortOrder = 'desc'
    elif pos <= -1 and  offset <= 0 :
        pos = int( math.fabs(pos))-1
        offset = int( math.fabs(offset))
        sortOrder = 'desc'
    elif pos == 0 and offset ==0:
        sortOrder = 'asc'
        pos = 0
        offset = 1
    elif 0 <= pos and 0 <= offset:
        sortOrder = 'asc'
    else: return None

    resp = client.search(index='action_traces', filter_path=['hits.hits._*'],
                         size=offset, from_=pos,
                         body={
                             "query":
                                 {"multi_match":
                                    {
                                       "query": account_name,
                                        "fields": ["act.account", "receipt.receiver", "act.data"]
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

def seeking_actions_to_from(account_name, from_date, to_date):

    if isinstance(from_date, int):
        es_from_date = datetime.datetime.utcfromtimestamp(from_date).strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        es_from_date = from_date
    if isinstance(to_date, int):
        es_to_date = datetime.datetime.utcfromtimestamp(to_date).strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        es_to_date = to_date

    resp = client.search(index='action_traces', filter_path=['hits.hits._*'], size = 10000,
                         body={
                             "query": {
                                 "bool": {
                                     "must": [
                                         {"multi_match":
                                              {"query": account_name,
                                               "fields": ["act.account", "receipt.receiver", "act.data"]
                                               }}],
                                     "filter": [
                                         {"range": {"block_time": {"gte": es_from_date, "lt": es_to_date}}}
                                     ]
                                 }},
                             "sort": [
                                 {"block_time": {"order": "desc"}}
                             ],
                             "timeout": "20s"
                         }
                         )

    if len(resp) == 0:
        return None

    result = []

    for field in resp['hits']['hits']:
        result.append(field['_source'])

    return {"actions": result}



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500, debug=True)
    app.config['JSON_AS_ASCII'] = False
