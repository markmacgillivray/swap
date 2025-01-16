import os
from functools import wraps
from flask import request, current_app

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders

from portality.core import app


def send_mail(to, fro, subject, text, files=[], bcc=[]):
    assert type(to)==list
    assert type(files)==list
    if bcc and not isinstance(bcc, list):
        bcc = [bcc]

    if app.config.get('CC_ALL_EMAILS_TO'):
        bcc.append(app.config.get('CC_ALL_EMAILS_TO'))
 
    msg = MIMEMultipart()
    msg['From'] = fro
    msg['To'] = COMMASPACE.join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
 
    msg.attach( MIMEText(text) )
 
    for file in files:
        part = MIMEBase('application', "octet-stream")
        if isinstance(file,dict):
            part.set_payload( file['content'] )
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="' + file['filename'] + '"')
        else:
            part.set_payload( open(file,"rb").read() )
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"'
                           % os.path.basename(file))
        msg.attach(part)
    
    # now deal with connecting to the server
    server = app.config.get("SMTP_SERVER", "localhost")
    server_port = app.config.get("SMTP_PORT", 25)
    smtp_user = app.config.get("SMTP_USER")
    smtp_pass = app.config.get("SMTP_PASS")
    
    smtp = smtplib.SMTP()  # just doing SMTP(server, server_port) does not work with Mailtrap
    # but doing .connect explicitly afterwards works both with Mailtrap and with Mandrill
    smtp.connect(server, server_port)

    if smtp_user is not None:
        smtp.login(smtp_user, smtp_pass)

    smtp.sendmail(fro, to + bcc, msg.as_string())
    smtp.close()


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
        
