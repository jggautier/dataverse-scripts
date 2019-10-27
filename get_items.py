# Python script for getting list of items from a Dataverse installation, using Search API and iterating through pages of results

import urllib2
import json
server = 'https://dataverse.harvard.edu' # Base URL of Dataverse installation, e.g. https://demo.dataverse.org
rows = 10
start = 0
page = 1
condition = True
text_file = open("items.txt", "w") # File with list of items is saved as items.txt
query = '*&type=dataverse' # query string for search API, e.g. '*&type=dataverse'
while (condition):
    url = server + '/api/search?q=' + query + "&start=" + str(start)
    data = json.load(urllib2.urlopen(url))
    total = data['data']['total_count']
    print "start:", start, " total:", total
    for i in data['data']['items']: # path to object in the Search APIs json
        text_file.write(i['identifier'] + "\n") # name of object to collect
    start = start + rows
    page += 1
    condition = start < total
text_file.close()
