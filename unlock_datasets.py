'''
curl "https://dataverse.harvard.edu/api/datasets/{database_id}/locks

Check for dataset locks:
curl "https://dataverse.harvard.edu/api/datasets/:persistentId/locks?persistentId=doi:10.7910/DVN/LK9GX"

Remove dataset locks:
curl -X DELETE -H "X-Dataverse-key: f6fb376a-6244-4b0d-b271-6963c563d02c" "https://dataverse.harvard.edu/api/datasets/:persistentId/locks?persistentId=doi:10.7910/DVN/LK9GX"
'''

import requests
import os

apikey='f6fb376a-6244-4b0d-b271-6963c563d02c'

pids=['doi:10.7910/DVN/NIJ3HD','doi:10.7910/DVN/KU8TBV','doi:10.7910/DVN/7IIDN','doi:10.7910/DVN/NJUBS','doi:10.7910/DVN/EMW91','doi:10.7910/DVN/HJFAJE','doi:10.7910/DVN/FNBMSZ','doi:10.7910/DVN/KX6Z2','doi:10.7910/DVN/2OBMN','doi:10.7910/DVN/RREOY','doi:10.7910/DVN/N3NL3Q','doi:10.7910/DVN/LRSMZ','doi:10.7910/DVN/WNLO47','doi:10.7910/DVN/VJNBZ','doi:10.7910/DVN/YJFUO','doi:10.7910/DVN/ENNRB','doi:10.7910/DVN/NBPWN','doi:10.7910/DVN/O02JK6','doi:10.7910/DVN/ECMYOS','doi:10.7910/DVN/ZQO7HV','doi:10.7910/DVN/SE1YWI','doi:10.7910/DVN/HL3J5D','doi:10.7910/DVN/892BX2','doi:10.7910/DVN/ZTFP5O','doi:10.7910/DVN/44I1CY','doi:10.7910/DVN/FJXIS','doi:10.7910/DVN/XWDMQT','doi:10.7910/DVN/BOEZMW','doi:10.7910/DVN/VF3GRC','doi:10.7910/DVN/Z9MMD6']

count=1

for pid in pids:
	url='https://dataverse.harvard.edu/api/datasets/:persistentId/locks?persistentId=%s' %(pid)
	r=requests.delete(url, headers={'X-Dataverse-key': apikey})
	print('Unlocked %s, %s of %s datasets' %(pid, count, len(pids)))
	count+=1