from flask import Flask
from flask_superadmin import Admin, model

from utils import install_models


#For using with django
from django.conf import settings

settings.configure(
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'mydatabase.sqlite',
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
    text = models.TextField()
    date = models.DateField()
    user = models.ForeignKey(User)
    def __unicode__(self):
        return self.title


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'

    # Build the manifest of apps and models that are to be synchronized

if __name__ == '__main__':
    # Create admin
    admin = Admin(app, 'Simple Models')

    # Add views
    admin.register(User)
    admin.register(Post)

    # Create tables in database if not exists
    try:
        install_models(User,Post)
    except:
        pass

    # Start app
    app.debug = True
    app.run('0.0.0.0', 8000)
