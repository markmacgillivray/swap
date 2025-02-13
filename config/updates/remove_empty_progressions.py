# a python script to remove empty progressions records
import requests

# read the app.cfg file one folder up to get the DB connection data
cfg = False
es_host = False
es_key = False
headers = {'Content-Type': 'application/json'}


def work():
    res = requests.get(es_host + 'swap_progression/_search?rest_total_hits_as_int=true&q=NOT access_course_college:*&size=9999', headers=headers)
    print('Found', res.json()['hits']['total'], 'to work on')
    worked = 0
    for hit in res.json()['hits']['hits']:
        rec = hit['_source']
        print('Deleting', rec['id'])
        r = requests.delete(es_host + 'swap_progression/_doc/' + rec['id'], headers=headers)
        print(r.status_code, r.text)
        worked += 1
    print('Worked on', worked, 'records')



try:
    cfg = open("../../app.cfg", "r")
except:
    print("Error reading app.cfg")
    try:
        cfg = open("../../portality/default_settings.py", "r")
    except:
        print("Error reading portality/default_settings.py")

try:
    for line in cfg:
        if "ELASTIC_SEARCH_HOST" in line:
            es_host = line.split(" = ")[1].strip().replace("'", "").replace('"', '')
        elif "ELASTIC_SEARCH_APIKEY" in line:
            es_key = line.split(" = ")[1].strip().replace("'", "").replace('"', '')

    cfg.close()

    if es_host:
        es_host = es_host.rstrip('/') + '/'
        if es_key:
            print('Using API key in headers', es_key)
            headers['Authorization'] = 'ApiKey ' + es_key
        print('Testing connection to index ...', es_host)
        reachable = requests.get(es_host + '/_search?rest_total_hits_as_int=true', headers=headers)
        if reachable.status_code == 200:
            print('Index reachable')
            try:
                work()
                print("Work done")
            except Exception as e:
                print("Error doing the work")
                print(e)
        else:
            print('Index not reachable, please check settings')

except:
    print("Could not find config for ES connection, no progress made")