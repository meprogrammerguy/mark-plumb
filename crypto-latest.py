#!/usr/bin/env python3

#This example uses Python 3.9.5 and the python-request library.

import urllib.request
import json
import http.client
import pprint

url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?start=1&limit=5000&convert=USD'

headers = {
  'Accepts': 'application/json',
  'X-CMC_PRO_API_KEY': '6fe0163a-ebe2-43bd-85de-eccb14a1e973',
}

connection = http.client.HTTPSConnection('pro-api.coinmarketcap.com', 443, timeout = 30)
connection.request('GET', url, None, headers)
try:
  response = connection.getresponse()
  content = response.read()
  returnContent = json.loads(content.decode('utf-8'))
  pprint.pprint(returnContent)
except http.client.HTTPException as e:
  print(e)
