from nose.tools import eq_, ok_, raises

import wtforms

from flask import Flask
from flask_superadmin import Admin


from django.conf import settings


settings.configure(
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'mydatabase.sqlite',
        }
    }
)

app = Flask(__name__)
app.config['SECRET_KEY'] = '123456790'
app.config['WTF_CSRF_ENABLED'] = False

admin = Admin(app)

from flask_superadmin.model.backends.django.view import ModelAdmin
from django.db import models, DatabaseError
from examples.django.utils import install_models


class CustomModelView(ModelAdmin):
    def __init__(self, model, name=None, category=None, endpoint=None,
                 url=None, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        super(CustomModelView, self).__init__(model, name, category, endpoint,
                                              url)

def test_list():
    class Person(models.Model):
        name = models.CharField(max_length=255)
        age = models.IntegerField()

        def __unicode__(self):
            return self.name

    # Create tables in the database if they don't exists
    try:
        install_models(Person)
    except DatabaseError as e:
        if 'already exists' not in e.message:
            raise

    Person.objects.all().delete()

    view = CustomModelView(Person)
    admin.add_view(view)

    eq_(view.model, Person)
    eq_(view.name, 'Person')
    eq_(view.endpoint, 'person')
    eq_(view.url, '/admin/person')

    # Verify form
    with app.test_request_context():
        Form = view.get_form()
        ok_(isinstance(Form()._fields['name'], wtforms.TextField))
        ok_(isinstance(Form()._fields['age'], wtforms.IntegerField))

    # Make some test clients
    client = app.test_client()

    resp = client.get('/admin/person/')
    eq_(resp.status_code, 200)

    resp = client.get('/admin/person/add/')
    eq_(resp.status_code, 200)

    resp = client.post('/admin/person/add/',
                     data=dict(name='name', age='18'))
    eq_(resp.status_code, 302)

    person = Person.objects.all()[0]
    eq_(person.name, 'name')
    eq_(person.age, 18)

    resp = client.get('/admin/person/')
    eq_(resp.status_code, 200)
    ok_(person.name in resp.data)

    resp = client.get('/admin/person/%s/' % person.pk)
    eq_(resp.status_code, 200)

    resp = client.post('/admin/person/%s/' % person.pk, data=dict(name='changed'))
    eq_(resp.status_code, 302)

    person = Person.objects.all()[0]
    eq_(person.name, 'changed')
    eq_(person.age, 18)

    resp = client.post('/admin/person/%s/delete/' % person.pk)
    eq_(resp.status_code, 200)
    eq_(Person.objects.count(), 1)

    resp = client.post('/admin/person/%s/delete/' % person.pk, data={'confirm_delete': True})
    eq_(resp.status_code, 302)
    eq_(Person.objects.count(), 0)

