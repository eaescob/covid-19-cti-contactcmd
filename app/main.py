import os
import slack
import sqlalchemy

from flask import Flask
from flask import abort, jsonify
from flask import request

from flask_sqlalchemy import SQLAlchemy
from flask_heroku import Heroku

from sqlalchemy import column, exists, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm.attributes import flag_modified

app = Flask(__name__)
#app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

heroku = Heroku(app)
db = SQLAlchemy(app)
slack = slack.WebClient(token=os.environ['SLACK_API_TOKEN'])

slack_signing_secret = os.environ['SLACK_SIGNING_SECRET']
## helper functions

def validate_slack_signature():

def build_response(message):
    resp = { "blocks" : [
        { "type" : "section",
         "text" : {
             "type" : "mrkdwn",
             "text" : message
         }}
    ]}
    return resp

def get_slack_profile(user_id):
    contact_info = {}
    try:
        resp=slack.users_profile_get(user=user_id)
        if resp['ok']:
            contact_info= {
                'full_name' :   resp['profile']['real_name'],
                'display_name' :  resp['profile']['display_name'],
                'title' :  resp['profile']['title']
                }
        return contact_info
    except:
        pass
return None

##ORM
class CTIContact(db.Model):
    __tablename__ = 'cti_contacts'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(MutableDict.as_mutable(JSONB))

    def __init__(self, data):
        self.data = data

    def __repr__(self):
            return '<id {}>'.format(self.id)

class CTIHelp(db.Model):
        __tablename__ = 'cti_help'
        id = db.Column(db.Integer, primary_key=True)
        data = db.Column(MutableDict.as_mutable(JSONB))

        def __init__(self, data):
                sefl.data = data;

        def __repr__(self):
                return '<id {}>'.format(self.id)

##routes
##@app.errorhandler(Exception)
##def handle_exceptions(e):
##    return jsonify(error='An error has occurred, please contact @emilio'), 500

@app.errorhandler(403)
def not_authorized(e):
    return jsonify(error=str(e)), 403

@app.route('/listorgs', methods=['POST'])
def listorgs():
    text=request.form['text']
    user_name=request.form['user_name']
    token=request.form['token']

    secret_token=os.environ['LISTORGS_SECRET']

    all_ccs = db.session.query(CTIContact).all()

    message = "Current registered organizations:\n"
    for cc in all_ccs:
        message += '- ' + cc.data['organization'] + '\n'

    resp = build_response(message)
    return jsonify(resp)

@app.route('/listmembers', methods=['POST'])
def listmembers():
    text=request.form['text']
    user_name=request.form['user_name']
    token=request.form['token']

    secret_token=os.environ['LISTMEMBERS_SECRET']

    if token != secret_token:
        abort(403, description='Not authorized')

    if len(text) == 0:
        resp = build_response('Missing organization')
        return jsonify(resp)
    else:
        cc = db.session.query(CTIContact).filter(
        ##    CTIContact.data.contains({'organization' : text})
            func.lower(CTIContact.data['organization'].astext) == func.lower(text)
            ).first()

        if cc is None:
            resp = build_response('Organization {} not found'.format(text))
            return jsonify(resp)
        else:
            contacts = ""
            for contact in cc.data['contacts']:
                contact_info = get_slack_profile(contact)
                if contact_info is not None:
                    contact_str = "-  {} (<@{}>)".format(contact_info['full_name'], contact)
                else:
                    contact_str = "- {}".format(contact);
                contacts += contact_str + '\n'
            contacts=contacts.rstrip('\n')
            message = "Contacs for {}:\n {}".format(text, contacts)
            resp = build_response(message)
            return jsonify(resp)

@app.route('/addcontact', methods=['POST'])
def addcontact():
    text=request.form['text']
    user_name=request.form['user_name']
    token=request.form['token']
    user_id=request.form['user_id']

    secret_token=os.environ['ADDCONTACT_SECRET']

    if token != secret_token:
        abort(403, description='Not authorized')

    #error checking
    message = ""
    if len(text) == 0:
        message = "Missing organization(s) you want to be a member of"
    else:
        orgs = text.split(',')
        plural =""
        if len(orgs) > 0:
            plural="s"

        message = "You have been added to the following organization%s: %s" % (plural, orgs)
        for org in orgs:
            cc = db.session.query(CTIContact).filter(
                func.lower(CTIContact.data['organization'].astext) == func.lower(org)
            ).first()
            if cc is None:
                cc = CTIContact(
                    data = {'organization' : org,
                            'contacts' : [user_id]}
                )
                db.session.add(cc)
                db.session.commit()
            else:

                if user_id not in cc.data['contacts']:
                    cc.data['contacts'].append(user_id)
                    flag_modified(cc, 'data')
                    db.session.add(cc)
                    db.session.commit()
                else:
                    resp = build_response('Nice try, you already are part of {}'.format(org))
                    return jsonify(resp)

    resp = build_response(message)
    return jsonify(resp)
