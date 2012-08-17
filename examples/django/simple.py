from flask import Flask

from flask.ext import superadmin, wtf
from flask.ext.superadmin.contrib import djangomodel

from utils import install_models


#For using with django
from django.conf import settings

settings.configure(
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'mydatabase',
        }
    }
)

from django.db import models


# Create application

app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'


class User(models.Model):
    class Meta:
        app_label = 'users'
    username = models.CharField(max_length=255,unique=True)
    email = models.CharField(max_length=255,unique=True)
    def __unicode__(self):
        return self.username


class Post(models.Model):
    class Meta:
        app_label = 'posts'
    title = models.CharField(max_length=255)
    # tags = db.ListField(db.StringField())
    text = models.TextField()
    date = models.DateField()
    user = models.ForeignKey(User)
    # complex = db.ListField(db.EmbeddedDocumentField(ComplexEmbedded))
    def __unicode__(self):
        return self.title
# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'

    # Build the manifest of apps and models that are to be synchronized
try:
    install_models(User,Post)
except:
    pass

if __name__ == '__main__':
    # Create admin
    admin = superadmin.Admin(app, 'Simple Models')

    # Add views
    admin.add_view(djangomodel.ModelView(User))
    admin.add_view(djangomodel.ModelView(Post))


    # Start app
    app.debug = True
    app.run('0.0.0.0', 8000)
