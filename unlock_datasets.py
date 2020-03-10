import urllib.request

server=''
apikey=''

pids=[]

count=0

for pid in pids:
	url='%s/api/datasets/:persistentId/locks?persistentId=%s' %(server, pid)

	headers={
		'X-Dataverse-key':apikey
		}

	req=urllib.request.Request(
		url=url,
		headers=headers,
		method='DELETE'
		)

	response=urllib.request.urlopen(req)

	count+=1

	print('Unlocked %s, %s of %s datasets' %(pid, count, len(pids)))