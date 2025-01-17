import json, requests, uuid

from collections import UserDict
from datetime import datetime

from portality.core import app, current_user

'''
All models in models.py should inherit this DomainObject to know how to save themselves in the index and so on.
You can overwrite and add to the DomainObject functions as required. See models.py for some examples.
'''
    
    
class DomainObject(UserDict):
    __type__ = None # set the type on the model that inherits this

    def __init__(self, **kwargs):
        if '_source' in kwargs:
            self.data = dict(kwargs['_source'])
            self.meta = dict(kwargs)
            del self.meta['_source']
        else:
            self.data = dict(kwargs)


    @classmethod
    def target(cls, kind, id):
        t = str(app.config['ELASTIC_SEARCH_HOST']) + '/'
        if kind == 'bulk':
            t += '_bulk'
        elif kind == 'scroll' and id:
            t += '_search/scroll?scroll=2m&scroll_id=' + id
        else:
            t += app.config['ELASTIC_SEARCH_DB'] + '_' + cls.__type__ + '/'
            t += '_' + ('search' if kind == 'scroll' else kind) # search, mapping (initial scroll goes to search, only subsequent ones go to /_scroll/search as above)
        if id and kind != 'scroll':
            if not t.endswith('/'): t += '/'
            t += id
        if kind == 'search' or kind == 'scroll':
            t += '?' if '?' not in t else '&'
            t += 'rest_total_hits_as_int=true'
            if kind == 'scroll' and not id: t += '&scroll=2m'
        return t
    
    @classmethod
    def send(cls, action, kind, id, data):
        print('in send', action, kind, id)
        headers = {}
        if isinstance(data, dict):
            data = json.dumps(data)
            headers['Content-Type'] = 'application/json'
        if app.config.get('ELASTIC_SEARCH_APIKEY', None):
            headers['Authorization'] = 'ApiKey ' + app.config['ELASTIC_SEARCH_APIKEY']
        if action == 'post':
            print('doing post', cls.target(kind, id))
            return requests.post(cls.target(kind, id), data=data, headers=headers)
        elif action == 'put':
            return requests.put(cls.target(kind, id), data=data, headers=headers)
        elif action == 'delete':
            return requests.delete(cls.target(kind, id), headers=headers)
        else:
            return requests.get(cls.target(kind, id), headers=headers)
    
    @classmethod
    def makeid(cls):
        '''Create a new id for data object
        overwrite this in specific model types if required'''
        return uuid.uuid4().hex

    @property
    def id(self):
        return self.data.get('id', None)
        
    @property
    def version(self):
        return self.meta.get('_version', None)

    @property
    def json(self):
        return json.dumps(self.data)

    @classmethod
    def prep(cls, rec):
        if 'id' in rec:
            id_ = rec['id'].strip()
        else:
            id_ = cls.makeid()
            rec['id'] = id_
        
        rec['last_updated'] = datetime.now().strftime("%Y-%m-%d %H%M")

        if 'created_date' not in rec:
            rec['created_date'] = datetime.now().strftime("%Y-%m-%d %H%M")
            
        if 'author' not in rec:
            try:
                rec['author'] = current_user.id
            except:
                rec['author'] = "anonymous"
                
        return rec


    def save(self):
        self.data = self.prep(self.data)
        r = self.send('post', 'doc', self.data['id'], self.data)

    def save_from_form(self,request):
        newdata = request.json if request.json else request.values
        for k, v in newdata.items():
            if k not in ['submit']:
                self.data[k] = v
        self.save()

    def bulk(cls, recs, idkey='id'):
        data = ''
        for r in recs:
            r = cls.prep(r)
            data += json.dumps( {'index':{'_id':r[idkey], '_index': app.config['ELASTIC_SEARCH_DB'] + '_' + cls.__type__}} ) + '\n'
            data += json.dumps( r ) + '\n'
        r = cls.send('post', 'bulk', None, data)
        return r.json()

    @classmethod
    def pull(cls, id_):
        '''Retrieve object by id.'''
        if id_ is None:
            return None
        try:
            out = cls.send('get', 'doc', id_, None)
            if out.status_code == 404:
                return None
            else:
                return cls(**out.json())
        except:
            return None

    @classmethod
    def mapping(cls):
        r = cls.send('get', 'mapping', None, None)
        return r.json()
        

    @classmethod
    def query(cls, q='', terms=None, facets=None, **kwargs):
        '''Perform a query on backend.

        :param q: maps to query_string parameter if string, or query dict if dict.
        :param terms: dictionary of terms to filter on. values should be lists. 
        :param facets: dict of facets to return from the query.
        :param kwargs: any keyword args as per
            http://www.elasticsearch.org/guide/reference/api/search/uri-request.html
        '''
        if isinstance(q,dict):
            query = q
        elif q:
            query = {'query': {'query_string': { 'query': q }}}
        else:
            query = {'query': {'match_all': {}}}

        try:
            query['query']['bool'] = query['query']['filtered']['query']['bool']
            query['query']['bool']['filter'] = query['query']['filtered']['filter']
            del query['query']['filtered']
        except:
            pass

        if facets:
            if 'facets' not in query:
                query['facets'] = {}
            for k, v in facets.items():
                query['facets'][k] = {"terms":v}

        if 'facets' in query:
            query['aggregations'] = query['facets']
            del query['facets']

        if terms:
            boolean = {'must': [] }
            for term in terms:
                if not isinstance(terms[term],list): terms[term] = [terms[term]]
                for val in terms[term]:
                    obj = {'term': {}}
                    obj['term'][ term ] = val
                    boolean['must'].append(obj)
            if q and not isinstance(q,dict):
                boolean['must'].append( {'query_string': { 'query': q } } )
            elif q and 'query' in q:
                boolean['must'].append( query['query'] )
            query['query'] = {'bool': boolean}

        for k,v in kwargs.items():
            if k == '_from':
                query['from'] = v
            else:
                query[k] = v

        if 'query' in query and 'bool' not in query['query']: query['query'] = {'bool': {'must': [], 'filter': [query['query']]}}
        if 'bool' not in query['query']: query['query']['bool'] = {'must': [], 'filter': []}
        if 'filter' not in query['query']['bool']: query['query']['bool']['filter'] = []

        try:
            # order: (default) count is highest count first, reverse_count is lowest first. term is ordered alphabetical by term, reverse_term is reverse alpha
            ords = {'count': {'_count': 'desc'}, 'reverse_count': {'_count': 'asc'}, 'term': {'_key': 'asc'}, 'reverse_term': {'_key': 'desc'}} # convert for ES7.x
            for ag, val in query['aggregations'].items():
                try:
                    if val['terms']['order'] in ords: query['aggregations'][ag]['terms']['order'] = ords[val['terms']['order']]
                except:
                    pass
        except:
            pass

        try:
            st = json.dumps(query)
            if '.exact' in st: query = json.loads(st.replace('.exact', '.keyword'))
        except:
            pass

        if 'size' not in query: query['size'] = 10
        if 'sort' not in query: query['sort'] = ['_doc']
        qt = 'search' if query['size'] <= app.config.get('MAX_QUERY_SIZE',10000) else 'scroll' # max_result_window can be configured in index settings, but not on serverless providers
        total = query['size']
        if qt == 'scroll': query['size'] = app.config.get('MAX_QUERY_SIZE',10000)
        if app.config.get('DEBUG',False): print(query)
        r = cls.send('post', qt, None, query)
        res = r.json()
        if res.get('hits', {}).get('total',0) > total: total = res['hits']['total']
        retrieved = len(res.get('hits',{}).get('hits',[]))
        prs = None
        scrollid = res.get('_scroll_id', None)
        # of course a for yield would be ideal but this will have to do for current refactor schedule
        while scrollid != prs and retrieved < total:
            #scrollid = scrollid.replace(/==$/, '') # is something like this needed for scrollid and/or prs? appears to be the case in the JS version
            r = cls.send('post', 'scroll', scrollid, None)
            rj = r.json()
            retrieved += len(rj['hits']['hits'])
            res['hits']['hits'] += rj['hits']['hits']
            prs = scrollid
            scrollid = rj.get('_scroll_id', None)
            if prs and prs != scrollid: cls.send('delete', 'scroll', prs, None)
        #if '_scroll_id' in res: del res['_scroll_id']

        if 'hits' in res and 'hits' in res['hits']:
            for hit in res['hits']['hits']:
                if hit.get('fields',None) != None and hit.get('_source',None) != None:
                    for k,v in hit['fields'].items():
                        hit['fields'][k] = hit['_source'][k]

        if 'aggregations' in res:
            res['facets'] = {}
            for k,v in res['aggregations'].items():
                res['facets'][k.replace('.keyword', '.exact')] = {'terms': [{'term': i['key'], 'count': i['doc_count']} for i in v['buckets']]}

        #if app.config.get('DEBUG',False): print(res)
        return res


    def delete(self):
        r = self.send('delete', 'doc', self.id, None)

    @classmethod
    def delete_all(cls):
        r = cls.send('delete', None, None, None)
        try:
            r = cls.send('put', 'mapping', None, app.config['MAPPINGS'][cls.__type__])
        except:
            pass
