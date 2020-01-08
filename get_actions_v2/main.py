import datetime
import re

from flask_cors import CORS, cross_origin
from flask import Flask, jsonify, request, abort, Response
import math
import json
import os
import requests as req

app = Flask(__name__)
CORS(app)

full_api = os.environ.get('GET_ACTIONS_ENDPOINT', "https://eos.greymass.com")

@app.route('/v2/history/get_actions', methods=['POST', 'OPTIONS', 'GET'])
@cross_origin()
def get_actions():
    account_name =request.get_json(force=True).get('account_name')
    action_name = request.get_json(force=True).get('action')

    if account_name == None:
        return 404
    position = -1
    offset = -100
    # offset = int(request.get('offset'))
    # position = int(request.get('pos'))
    # Form the default endpoint path
    endpoint = full_api + '/v1/history/get_actions'
    # Determine if this query fits in the limit history dataset
    # Create Request
    r = req.post(endpoint, json={
        "account_name": account_name,
        "pos": position,
        "offset": offset
    })
    jsonResponse = json.loads(r.text)
    actions = jsonResponse['actions']
    actionsTransfer = []
    for action in actions:
        if action['action_trace']['act']['name'] == "transfer":
            temp = {}
            temp['act'] = {}
            temp['act']['data'] = action['action_trace']['act']['data']
            temp['block_time'] = action['block_time']
            temp['act']['name'] = action['action_trace']['act']['name']
            temp['act']['account'] = action['action_trace']['act']['account']
            actionsTransfer.append(temp)

    response = {"actions": actionsTransfer}
    # Return response
    # resp.body = json.dumps(response, ensure_ascii=False)

    json_string = json.dumps(response,ensure_ascii = False)

    response = Response(json_string, content_type="application/json; charset=utf-8")
    return response



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500, debug=True)
    app.config['JSON_AS_ASCII'] = False
