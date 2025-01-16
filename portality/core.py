import os, requests, json, uuid, time
from flask import Flask

from portality import default_settings
from flask_login import LoginManager, current_user
login_manager = LoginManager()

from werkzeug.security import generate_password_hash

def create_app():
    app = Flask(__name__)
    configure_app(app)
    if app.config.get('INITIALISE_INDEX',False): initialise_index(app)
    login_manager.setup_app(app)
    return app

def configure_app(app):
    app.config.from_object(default_settings)
    # parent directory
    here = os.path.dirname(os.path.abspath( __file__ ))
    config_path = os.path.join(os.path.dirname(here), 'app.cfg')
    if os.path.exists(config_path): app.config.from_pyfile(config_path)

def initialise_index(app):
    if not app.config.get('ELASTIC_SEARCH_HOST',None) or not app.config.get('ELASTIC_SEARCH_DB',None):
        print("No ElasticSearch host or db specified, cannot initialise index")
        return

    try:
        print("Initialising index on", app.config['ELASTIC_SEARCH_HOST'], ",", app.config['ELASTIC_SEARCH_DB'], "...", app.config.get('ELASTIC_SEARCH_APIKEY', ''))
        headers = {'Content-Type': 'application/json'}
        if app.config.get('ELASTIC_SEARCH_APIKEY', None):
            headers['Authorization'] = 'ApiKey ' + app.config['ELASTIC_SEARCH_APIKEY']
        mappings = app.config.get("MAPPINGS",{})
        i = str(app.config['ELASTIC_SEARCH_HOST']).rstrip('/') + '/'
        print('Testing connection to index ...')
        reachable = requests.get(i + '/_search?rest_total_hits_as_int=true', headers=headers)
        print(reachable.status_code)
        print(reachable.text)
        if reachable.status_code == 200:
            print('Index reachable')
        else:
            print('Index not reachable, please check settings')
            return

        if app.config.get('UPLOAD_DATA',False): # do this separately from below where we upload, so that mapping gets put again first if necessary
            for key, fn in app.config['UPLOAD_DATA'].items():
                if app.config.get('UPLOAD_EMPTY_FIRST',{}).get(key,False): # could allow this even if not in upload data?
                    print('Deleting existing data for', key)
                    r = requests.delete(i + app.config['ELASTIC_SEARCH_DB'] + '_' + key, headers=headers)
                    print(key, r.status_code, r.text)

        for key, mapping in mappings.items():
            exists = requests.head(i + app.config['ELASTIC_SEARCH_DB'] + '_' + key, headers=headers)
            if exists.status_code != 200:
                r = requests.put(i + app.config['ELASTIC_SEARCH_DB'] + '_' + key, data=json.dumps(mapping), headers=headers)
                print('Creating index', key, ',', r.status_code)
                print(r.text)

        curr = requests.get(i + app.config['ELASTIC_SEARCH_DB'] + '_archive/_doc/current', headers=headers)
        if curr.status_code != 200:
            a = requests.post(i + app.config['ELASTIC_SEARCH_DB'] + '_archive/_doc/current', data=json.dumps({
                'name':'current',
                'id': 'current'
            }), headers=headers)
            print('Creating default archive named "current"', '...', curr.status_code, '...', a.status_code)
            print(a.text)
        else:
            print('Default archive exists')

        if len(app.config.get('SUPER_USER',[])) != 0:
            un = app.config['SUPER_USER'][0]
            ia = i + app.config['ELASTIC_SEARCH_DB'] + '_account/_doc/' + un
            ae = requests.get(ia, headers=headers)
            if ae.status_code != 200:
                pw = generate_password_hash(un)
                su = {
                    "id":un, 
                    "email":"test@test.com",
                    "api_key":str(uuid.uuid4()),
                    "password":pw
                }
                if app.config.get('CREATE_SUPER_USER',False):
                    c = requests.post(ia, data=json.dumps(su), headers=headers)
                    print("Creating first superuser account for user", un, "with password hash of username", pw, "...", c.status_code)
                    print(c.text)
                else:
                    print("First superuser account", un, "not created, please enable in config and restart or create manually")
            else:
                print("Superuser account", un, "exists")

        if app.config.get('UPLOAD_DATA',False):
            for key, fn in app.config['UPLOAD_DATA'].items():
                print('Uploading', key, 'from', fn)
                with open(fn, 'r') as f:
                    dump = json.load(f)
                    data = [d['_source'] for d in dump['hits']['hits']]
                    print('Uploading', len(data), 'records')
                    # convert data to ES bulk upload format and send
                    bulk = []
                    for d in data:
                        idx = {'index': {'_index': app.config['ELASTIC_SEARCH_DB'] + '_' + key}}
                        if 'id' in d: idx['index']['_id'] = d['id']
                        if '_id' in d: idx['index']['_id'] = d['_id']
                        bulk.append(idx)
                        bulk.append(d)
                    r = requests.post(i + '_bulk', data='\n'.join([json.dumps(b) for b in bulk]) + '\n', headers=headers)
                    print(r.status_code) #, r.text)
    except Exception as e:
        print("Index initialisation error:")
        print(e)


app = create_app()

