import urllib.request

server=''
apikey=''
DATA=b'distributionDate'
pids=[]
count=0

for pid in pids:

	url='%s/api/datasets/:persistentId/citationdate?persistentId=%s' %(server, pid)

	headers={
		'X-Dataverse-key':apikey
		}

	req=urllib.request.Request(
		url=url,
		data=DATA,
		headers=headers,
		method='PUT'
		)

	response=urllib.request.urlopen(req)

	count+=1

	print('Changing citation dates: %s of %s datasets' %(count, len(pid)), end='\r', flush=True)