import datetime
import re

from flask_cors import CORS, cross_origin
from flask import Flask, jsonify, request, abort, Response
from elasticsearch import Elasticsearch
import math
import json
import os

app = Flask(__name__)
CORS(app)

ELASTIC_HOST = os.environ['ELASTIC_HOST']
ELASTIC_PORT = os.environ['ELASTIC_PORT']
client = Elasticsearch([{'host': ELASTIC_HOST, 'port': ELASTIC_PORT}], timeout=30)

@app.route('/v1/history/get_actions', methods=['POST','OPTIONS','GET'])
@app.route('/v2/history/get_actions', methods=['POST','OPTIONS','GET'])
@cross_origin()
def get_actions():
    if request.headers['X-Forwarded-Host'] == 'api.worbli.eostribe.io':
        elasticIndex = "worbli_action_traces*"
    elif request.headers['X-Forwarded-Host'] == 'api.bos.eostribe.io':
        elasticIndex = "bos_action_traces*"
    elif request.headers['X-Forwarded-Host'] == 'api.telos.eostribe.io':
        elasticIndex = "telos_action_traces*"
    else:
        elasticIndex = "action_traces*"

    pos = request.get_json(force=True).get('pos')

    offset = request.get_json(force=True).get('offset')

    last = request.get_json(force=True).get('last')

    account_name =request.get_json(force=True).get('account_name')

    last_days = request.get_json(force=True).get('last_days')

    from_date = request.get_json(force=True).get('from_date')

    to_date = request.get_json(force=True).get('to_date')
    contract = request.get_json(force=True).get('contract')
    action_name = request.get_json(force=True).get('action')

    if account_name == None:
        return 404
    elif action_name != None:
        seeking_result = seeking_actions_last_days_action_filtered(account_name, str(last_days), action_name, elasticIndex)
    elif contract != None:
        seeking_result = seeking_actions_last_days_contract_filtered(account_name, str(last_days), contract, elasticIndex)
    elif last_days != None:
        seeking_result = seeking_actions_last_days(account_name, str(last_days), elasticIndex)
    elif last != None:
        seeking_result = seeking_actions_last(account_name, str(last), elasticIndex)
    elif from_date != None:
        seeking_result = seeking_actions_to_from(account_name,from_date,to_date, elasticIndex)
    elif pos == None and offset == None and last_days == None and from_date == None and to_date== None:
        seeking_result = seeking_actions_account_name(account_name, elasticIndex)
    else:
         seeking_result = seeking_actions(account_name,pos,offset, elasticIndex)
    if seeking_result is None:
        return abort(404)

    json_string = json.dumps(seeking_result,ensure_ascii = False)
    response = Response(json_string, content_type="application/json; charset=utf-8")
    return response


def seeking_actions_account_name(account_name, es_index):
    resp = client.search(index=es_index, filter_path=['hits.hits._*'], size = 10000,
         body={"query":{"bool":{
	          "must":[],
	                "filter":[
                        {"bool":
		                  {"should":[
                              {"bool":{"should":[{"match_phrase":
		                        {"act.authorization.actor":account_name}}],"minimum_should_match":1}},
		                      {"bool":{"should":[{"match_phrase":
		                        {"receipt.receiver":account_name}}],"minimum_should_match":1}}],
                           "minimum_should_match":1}}]}},
                    "sort": [{"block_time": {"order": "desc"}}],
                    "timeout": "10s"
                    }
                )

    if len(resp) == 0:
        return None

    return {"actions": get_result(resp)}

def seeking_actions_last_days(account_name, last_days,es_index):
    resp = client.search(index=es_index, filter_path=['hits.hits._*'], size = 10000,
        body={
          "query":{"bool":{
	          "must":[
                  {"range":{"block_time":{"gte":"now-"+str(last_days)+"d","lte":"now"}}}],
	          "filter":[{"bool":
		             {"should":[
                         {"bool":{"should":[{"match_phrase":
		                    {"act.authorization.actor":account_name}}],"minimum_should_match":1}},
		                 {"bool":{"should":[{"match_phrase":
		                   {"receipt.receiver":account_name}}],"minimum_should_match":1}}],"minimum_should_match":1}}]}},
        "sort": [{"block_time": {"order": "asc"}}],"timeout": "20s"
            })

    if len(resp) == 0:
        return None

    return {"actions": get_result(resp)}

def seeking_actions(account_name, pos, offset, es_index):
    if pos == -1 and offset == -1:
        pos = 0
        offset = 1
        sortOrder = "desc"
        sortColumn = "block_num"
    elif pos <= -1 and  offset <= 0 :
        pos = int( math.fabs(pos))-1
        offset = int( math.fabs(offset))
        sortOrder = 'desc'
        sortColumn = "block_num"
    elif pos == 0 and offset ==0:
        sortOrder = 'asc'
        pos = 0
        offset = 1
        sortColumn = "block_num"
    elif 0 <= pos and 0 <= offset:
        if offset == 0:
            offset+=1
        sortOrder = 'asc'
        sortColumn = "block_num"
    else: return None

    resp = client.search(index=es_index, filter_path=['hits.hits._*'],
                         size=offset, from_=pos,
            body={"query":{
                    "bool":{
                        "must": [],
                          "filter":
                              [{"bool":
                                  {"should":[{"bool":
                                               {"should": [{"match_phrase":
                                                    {"act.authorization.actor": account_name}}],"minimum_should_match": 1}},
                                            {"bool":
                                               {"should": [{"match_phrase":
                                                    {"receipt.receiver": account_name}}],"minimum_should_match": 1}}],"minimum_should_match": 1}}]}},
                             "sort": [
                                 {sortColumn: {"order": sortOrder}}
                             ],
                             "timeout": "10s"
                         })
    if len(resp) == 0:
        return None

    return {"actions": get_result(resp)}

def seeking_actions_to_from(account_name, from_date, to_date, es_index):

    if isinstance(from_date, int):
        es_from_date = datetime.datetime.utcfromtimestamp(from_date).strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        es_from_date = from_date

    if to_date == None:
        es_to_date = "now"
    elif isinstance(to_date, int):
        es_to_date = datetime.datetime.utcfromtimestamp(to_date).strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        es_to_date = to_date

    resp = client.search(index=es_index, filter_path=['hits.hits._*'], size = 10000,
        body={
            "query":{"bool":{
	          "must":[
		        {"range":{
		           "block_time":{"gte":es_from_date,"lte":es_to_date}}}],
	                "filter":[{"bool":
		             {"should":[{"bool":
		              {"should":[{"match_phrase":
		               {"act.authorization.actor":account_name}}],"minimum_should_match":1}},
		              {"bool":{"should":[{"match_phrase":
		               {"receipt.receiver":account_name}}],"minimum_should_match":1}}],"minimum_should_match":1}}]}},
             "sort": [{"block_time": {"order": "desc"}}],"timeout": "20s"
            })

    if len(resp) == 0:
        return None

    return {"actions": get_result(resp)}

def seeking_actions_last(account_name,last,es_index):

    if re.fullmatch(r"([0-9]+)([y,M,w,d,h,H,m,s])", last) == None:
        return None

    resp = client.search(index=es_index, filter_path=['hits.hits._*'], size = 10000,
        body={
          "query":{"bool":{
	          "must":[
		        {"range":{
		           "block_time":{"gte":"now-"+last,"lte":"now"}}}],
	                "filter":[{"bool":
		             {"should":[{"bool":
		              {"should":[{"match_phrase":
		               {"act.authorization.actor":account_name}}],"minimum_should_match":1}},
		              {"bool":{"should":[{"match_phrase":
		               {"receipt.receiver":account_name}}],"minimum_should_match":1}}],"minimum_should_match":1}}]}},
                             "sort": [
                                 {"block_time": {"order": "asc"}}],"timeout": "90s"})

    if len(resp) == 0:
        return None

    return {"actions": get_result(resp)}

def seeking_actions_last_days_action_filtered(account_name, last_days,action_name, es_index):
    resp = client.search(index=es_index, filter_path=['hits.hits._*'], size = 10000,
        body={
           "query": {"bool": {"must": [
                   {"range": {"block_time": {"gte": "now-"+str(last_days)+"d", "lte": "now"}}},
                   {"match_phrase": {"act.name": {"query": action_name}}}],
                "filter": [{"bool": {"should": [
                              {"bool": {"should": [
                                  {"match_phrase": {"act.authorization.actor": account_name}}],"minimum_should_match": 1}},
                              {"bool": {"should": [{
                                 "match_phrase": {"receipt.receiver": account_name}}],"minimum_should_match": 1}}
                                                ],"minimum_should_match": 1}}]}},
            "sort": [{"block_time": {"order": "asc"}}],"timeout": "20s"
        })

    if len(resp) == 0:
        return None

    return {"actions": get_result(resp)}

def seeking_actions_last_days_contract_filtered(account_name, last_days,contract, es_index):
    resp = client.search(index=es_index, filter_path=['hits.hits._*'], size = 10000,
        body={"query": {"bool": {"must": [
                   {"range": {"block_time": {"gte": "now-"+str(last_days)+"d", "lte": "now"}}},
                   {"match_phrase": {"act.account": {"query": contract}}}],
                "filter": [{"bool": {"should": [
                              {"bool": {"should": [
                                  {"match_phrase": {"act.authorization.actor": account_name}}],"minimum_should_match": 1}},
                              {"bool": {"should": [{
                                 "match_phrase": {"receipt.receiver": account_name}}],"minimum_should_match": 1}}
                                              ],"minimum_should_match": 1}}]}},
            "sort": [{"block_time": {"order": "asc"}}],"timeout": "20s"
                         }
                         )

    if len(resp) == 0:
        return None

    return {"actions": get_result(resp)}


def get_result(resp):
    result = []
    cache = []
    for field in resp['hits']['hits']:
        if field['_source']['receipt']['act_digest'] not in cache:
            field['_source']['act']['data'] = json.loads(field['_source']['act']['data'])
            result.append(field['_source'])
            cache.append(field['_source']['receipt']['act_digest'])
    return result


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500, debug=True)
    app.config['JSON_AS_ASCII'] = False
