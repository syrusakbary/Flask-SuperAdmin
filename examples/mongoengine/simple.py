from flask import Flask
from flask_superadmin import Admin, model

try:
    from mongoengine import *
except ImportError:
    exit('You must have mongoengine installed. Install it with the command:\n\t$> easy_install mongoengine')

# Create application
app = Flask(__name__)

# Create dummy secret key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

mongodb_settings = {
    'db':'test',
    # 'username':None,
    # 'password':None,
    # 'host':None,
    # 'port':None
}

# Connect to mongodb
connect(**mongodb_settings)


# Defining MongoEngine Documents

class User(Document):
    username = StringField(unique=True)
    email = StringField(unique=True)
    def __unicode__(self):
        return self.username

class ComplexEmbedded (EmbeddedDocument):
    complexstring = StringField()
    multiple_users = ListField(ReferenceField('User'))

class Post(Document):
    user = ReferenceField(User)
    tags = ListField(StringField())
    text = StringField()
    date = DateTimeField()
    complex = ListField(EmbeddedDocumentField(ComplexEmbedded))


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'

if __name__ == '__main__':
    
    # Create admin
    admin = Admin(app, 'Simple Models')

    class UserModel(model.ModelAdmin):
        list_display = ('username','email')
        # only = ('username',)

    # Register the models
    admin.register(User, UserModel)
    admin.register(Post)

    # Start app
    app.debug = True
    app.run('0.0.0.0', 8000)
