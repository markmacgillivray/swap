
from functools import wraps
from flask import request, current_app

from portality.core import app


def dewindows(string):
    try:
        string = string.decode("windows-1252")
    except:
        try:
            string = string.decode("windows-1251")
        except:
            try:
                string = string.decode("ISO-8859-1")
            except:
                try:
                    string = string.decode("utf-8")
                except:
                    pass
    return string


def jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            try:
                content = str(callback) + '(' + str(f(*args,**kwargs).data.decode()) + ')'
            except:
                content = str(callback) + '(' + str(f(*args,**kwargs).data) + ')'
            return current_app.response_class(content, mimetype='application/javascript')
        else:
            return f(*args, **kwargs)
    return decorated_function


# derived from http://flask.pocoo.org/snippets/45/ (pd) and customised
def request_wants_json():
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    if best == 'application/json' and request.accept_mimetypes[best] > request.accept_mimetypes['text/html']:
        best = True
    else:
        best = False
    if request.values.get('format','').lower() == 'json' or request.path.endswith(".json"):
        best = True
    return best
        
