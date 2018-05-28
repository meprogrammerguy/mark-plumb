#!/usr/bin/env python
import http.client
import pdb
import pprint
import json

# Request: Market Quotes (https://sandbox.tradier.com/v1/markets/quotes?symbols=spy)
connection = http.client.HTTPSConnection('sandbox.tradier.com', 443, timeout = 30)

# Headers

headers = {"Accept":"application/json",
    "Authorization":"Bearer j1AmwxGRVuqhtM1OzSAwy8ftbdkn",
    "connection":"close"}

# Send synchronously
url = "/v1/markets/calendar"
connection.request('GET', url, None, headers)
try:
  response = connection.getresponse()
  content = response.read()
  returnContent = json.loads(content)
  pprint.pprint(returnContent)
  #print (returnContent)
  # Success
  print('Response status ' + str(response.status))
except http.client.HTTPException as e:
  # Exception
  print('Exception during request')
