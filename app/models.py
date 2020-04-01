from . import db
from sqlalchemy.dialects.postgresql import JSONB

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
