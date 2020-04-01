import os
import sqlalchemy


from flask import Flask
from flask import jsonify
from flask import request

from flask_sqlalchemy import SQLAlchemy
from flask_heroku import Heroku

from sqlalchemy.dialects.postgresql import JSONB

app = Flask(__name__)
#app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

heroku = Heroku(app)
db = SQLAlchemy(app)

## helper functions
def build_response(message):
    resp = { "blocks" : [
        { "type" : "section",
         "text" : {
             "type" : "mrkdwn",
             "text" : message
         }}
    ]}
    return resp

##ORM
class CTIContact(db.Model):
    __tablename__ = 'cti_contacts'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(JSONB)

    def __init__(self, data):
        self.data = data

    def __repr__(self):
            return '<id {}>'.format(self.id)

class CTIHelp(db.Model):
        __tablename__ = 'cti_help'
        id = db.Column(db.Integer, primary_key=True)
        data = db.Column(JSONB)

        def __init__(self, data):
                sefl.data = data;

        def __repr__(self):
                return '<id {}>'.format(self.id)

##routes

@app.route('/listmembers', methods=['POST'])
def listmembers():
    text=request.form['text']
    user_name=request.form['user_name']

    if len(text) == 0:
        resp = build_resonse('Missing organization')
        return jsonify(resp)
    else:
        cc = CTIContact.query.filter(
            CTIContact.data[
                ('organization')
            ].cast(sqlalchemy.Text) == text
        ).one()

        if cc is None:
            resp = build_response('Organization {} not found'.format(text))
            return jsonify(resp)
        else:
            message = "Contacs for {} : {}".format(text, cc.data['contacts'])
            resp = build_response(message)
            return jsonify(resp)

@app.route('/addcontact', methods=['POST'])
def addcontact():
    text=request.form['text']
    user_name=request.form['user_name']

    #error checking
    response = ""
    if len(text) == 0:
        message = "Missing organization(s) you want to be a member of"
    else:
        orgs = text.split(',')
        plural =""
        if len(orgs) > 0:
            plural="s"

        message - "You have been added to the following organization%s: %s" % (plural, orgs)
        for org in orgs:
            cc = CTIContact.query.filter(
                CTIContact.data[
                    ('organization')
                ].cast(sqlalchemy.Text) == org
            ).one()
            if cc is None:
                cc = CTIContact(
                    data = {'organization' : org,
                            'contacts' : [user_name]}
                )
                db.session.add(cc)
                db.session.commit()
            else:
                cc.data['contacts'].append(user_name)
                db.session.commit()

    resp = build_response(message)
    return jsonify(resp)
