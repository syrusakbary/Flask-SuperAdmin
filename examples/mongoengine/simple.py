#mongoengine
#https://github.com/sbook/flask-mongoengine/tarball/master

from flask import Flask
from flaskext.mongoengine import MongoEngine

from flask.ext import superadmin, wtf
from flask.ext.superadmin.contrib import mongoenginemodel

# Create application

app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['MONGODB_DB'] = 'test'
db = MongoEngine(app)

class User(db.Document):
    username = db.StringField(unique=True)
    email = db.StringField(unique=True)
    def __unicode__(self):
        return self.username

class ComplexEmbedded (db.EmbeddedDocument):
    complexstring = db.StringField()
    multiple_users = db.ListField(db.ReferenceField('User'))

class Post(db.Document):
    user = db.ReferenceField(User)
    tags = db.ListField(db.StringField())
    text = db.StringField()
    date = db.DateTimeField()
    complex = db.ListField(db.EmbeddedDocumentField(ComplexEmbedded))
# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


# Customized Post model admin

if __name__ == '__main__':
    # Create admin
    admin = superadmin.Admin(app, 'Simple Models')

    # Add views
    admin.add_view(mongoenginemodel.ModelView(User))
    admin.add_view(mongoenginemodel.ModelView(Post))


    # Start app
    app.debug = True
    app.run('0.0.0.0', 8000)
