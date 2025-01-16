from datetime import timedelta

SECRET_KEY = "default-key" # make this something secret in your overriding app.cfg
REMEMBER_COOKIE_DURATION = timedelta(minutes=60)
PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)

# contact info
ADMIN_NAME = "SWAP"
ADMIN_EMAIL = ""

# service info
SERVICE_NAME = "SWAP"
HOST = "0.0.0.0"
DEBUG = True
PORT = 5006

# list of superuser account names
SUPER_USER = ["test"]
CREATE_SUPER_USER = False # whether or not to create the superuser account if it does not exist (and if initialising the index, see below)
PUBLIC_REGISTER = False # Can people register publicly? If false, only the superuser can create new accounts

# elasticsearch settings
ELASTIC_SEARCH_HOST = "http://127.0.0.1:9200"
ELASTIC_SEARCH_DB = "swap"
INITIALISE_INDEX = False # whether or not to try creating the index and required index types on startup
NO_QUERY_VIA_API = ['account','student'] # list index types that should not be queryable via the API


FACET_FIELD = ".keyword" # identifier for how non-analyzed fields for faceting are differentiated in the mappings
# dict of ES mappings, settings, aliases if necessary. identify index by key name. Put the mapping in a "mapping" key. 
# if no settings mappings or aliases are needed for a type, set the value to {}
# otherwise provide any needed as per https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-create-index.html
MAPPINGS = {"student" : {}}
MAPPINGS['account'] = MAPPINGS["student"] # if needed to just copy a mapping to another index, do like this
MAPPINGS['course'] = {}
MAPPINGS['simd'] = {}
MAPPINGS['progression'] = {}
MAPPINGS['uninote'] = {}
MAPPINGS['archive'] = {}
MAPPINGS['schoolsubject'] = {}
MAPPINGS['schoollevel'] = {}
MAPPINGS['postschoollevel'] = {}

#UPLOAD_DATA = {} # key should match an index name above, and value should be the file location to bulk upload
UPLOAD_DATA = {
  #"student" : "/home/leaps/MOVE/swap/swap_student.json",
  #"account" : "/home/leaps/MOVE/swap/swap_account.json",
  #"course" : "/home/leaps/MOVE/swap/swap_course.json",
  #"simd" : "/home/leaps/MOVE/swap/swap_simd.json"
  #"progression" : "/home/leaps/MOVE/swap/swap_progression.json",
  #"uninote" : "/home/leaps/MOVE/swap/swap_uninote.json",
  #"archive" : "/home/leaps/MOVE/swap/swap_archive.json",
  #"schoolsubject" : "/home/leaps/MOVE/swap/swap_schoolsubject.json",
  #"schoollevel" : "/home/leaps/MOVE/swap/swap_schoollevel.json",
  #"postschoollevel" : "/home/leaps/MOVE/swap/swap_postschoollevel.json"
}
#UPLOAD_EMPTY_FIRST = {} # key should match an index with value True if index should be emptied before upload - and only happens if in UPLOAD_DATA
UPLOAD_EMPTY_FIRST = {
  #"student" : True,
  #"account" : True,
  #"course" : True,
  #"simd" : True
  #"progression" : True,
  #"uninote" : True,
  #"archive" : True,
  #"schoolsubject" : True,
  #"schoollevel" : True,
  #"postschoollevel" : True
}