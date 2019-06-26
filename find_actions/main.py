import re
from flask_cors import CORS, cross_origin
from flask import Flask, jsonify, request, abort, Response
from elasticsearch import Elasticsearch
import datetime

import json
import os

app = Flask(__name__)
CORS(app)

ELASTIC_HOST = os.environ['ELASTIC_HOST']
ELASTIC_PORT = os.environ['ELASTIC_PORT']
client = Elasticsearch([{'host': ELASTIC_HOST, 'port': ELASTIC_PORT}], timeout=30)

@app.route('/v1/history/find_actions',methods=['POST','OPTIONS','GET'])
@app.route('/v2/history/find_actions',methods=['POST','OPTIONS','GET'])
@cross_origin()
def find_actions():
    if request.headers['X-Forwarded-Host'] == 'api.worbli.eostribe.io':
       elasticIndex = "worbli_action_traces*"
    elif request.headers['X-Forwarded-Host'] == 'api.bos.eostribe.io':
      elasticIndex = "bos_action_traces*"
    elif request.headers['X-Forwarded-Host'] == 'api.telos.eostribe.io':
      elasticIndex = "telos_action_traces*"
    elif request.headers['X-Forwarded-Host'] == 'api.meetone.eostribe.io':
      elasticIndex = "meetone_action_traces*"
    else:
      elasticIndex = "action_traces*"

    last_days = request.get_json(force=True).get('last_days')
    last = request.get_json(force=True).get('last')
    from_date = request.get_json(force=True).get('from_date')
    to_date =  request.get_json(force=True).get('to_date')
    data = request.get_json(force=True).get('data')

    if data == None:
        return ('', 204)
    elif last_days != None:
        seeking_result = seeking_actions_last_days(data, str(last_days), elasticIndex)
    elif from_date != None and to_date != None:
         seeking_result = seeking_actions_to_from(data,from_date,to_date, elasticIndex)
    elif last != None:
        seeking_result = seeking_actions_last(data, str(last), elasticIndex)
    elif last_days == None and from_date == None and to_date== None and last == None:
        seeking_result = seeking_actions(data, elasticIndex)
    else:
        return ('', 204)
    if seeking_result is None:
        return abort(404)

    json_string = json.dumps(seeking_result,ensure_ascii = False)
    response = Response(json_string, content_type="application/json; charset=utf-8")
    return response

def seeking_actions(data, es_index):
    resp = client.search(index=es_index, filter_path=['hits.hits._*'], size = 1000,
                         body={"query":
                                   {"bool": {"filter": [
                                       {"bool":
                                           {"must": [
                                               {"match_phrase":
                                                    {"act.data": data}}]
                                       }}]}},
                             "timeout": '20s'}
                         )
    if len(resp) == 0:
        return None

    result = []

    for field in resp['hits']['hits']:
        field['_source']['act']['data'] = json.loads(
            field['_source']['act']['data'])
        result.append(field['_source'])

    return {"actions":result}

def seeking_actions_last_days(data, last_days,es_index):
    resp = client.search(index=es_index, filter_path=['hits.hits._*'], size = 10000,
                         body={
                             "query": {
                                 "bool": {
                                     "must": [{
                                         "match_phrase":{
                                             "act.data": data}}],
                                     "filter": [
                                         {"range": {"block_time": {"gte": "now-" + last_days + "d/d", "lte": "now/d"}}}
                                     ]
                                 }},
                             "timeout": '20s'
                         }
                         )

    if len(resp) == 0:
        return None

    result = []

    for field in resp['hits']['hits']:
        field['_source']['act']['data'] = json.loads(
            field['_source']['act']['data'])
        result.append(field['_source'])
    return {"actions":result}

def seeking_actions_to_from(data, from_date, to_date, es_index):

    if isinstance(from_date, int):
        es_from_date = datetime.datetime.utcfromtimestamp(from_date).strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        es_from_date = from_date
    if isinstance(to_date, int):
        es_to_date = datetime.datetime.utcfromtimestamp(to_date).strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        es_to_date = to_date

    resp = client.search(index=es_index, filter_path=['hits.hits._*'], size = 10000,
                         body={
                             "query": {
                                 "bool": {
                                     "must": [
                                         {"match_phrase":
                                              {"act.data": data}}],
                                     "filter": [
                                         {"range": {"block_time": {"gte": es_from_date, "lte": es_to_date}}}
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
        field['_source']['act']['data'] = json.loads(
            field['_source']['act']['data'])
        result.append(field['_source'])

    return {"actions": result}

def seeking_actions_last(data,last,es_index):

    if re.fullmatch(r"([0-9]+)([y,M,w,d,h,H,m,s])", last) == None:
        return None

    resp = client.search(index=es_index, filter_path=['hits.hits._*'], size = 10000,
                         body={
                             "query": {
                                 "bool": {
                                     "must":[{
                                         "match_phrase":{
                                            "act.data":{
                                                "query": data}}}],
                                     "filter": [
                                         {"range": {"block_time": {"gte": "now-"+last, "lte":"now"}}}
                                     ]
                                 }},
                             "sort": [
                                 {"block_time": {"order": "asc"}}],
                             "timeout": "90s"
                         }
                         )
    if len(resp) == 0:

        return None

    result = []

    for field in resp['hits']['hits']:
        field['_source']['act']['data'] = json.loads(
            field['_source']['act']['data'])
        result.append(field['_source'])

    return {"actions": result}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500, debug=True)
    app.config['JSON_AS_ASCII'] = False

