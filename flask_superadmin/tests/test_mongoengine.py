from nose.tools import eq_, ok_, raises

from flask import Flask
from flask.ext import wtf
from mongoengine import *

from flask_superadmin import Admin
from flask_superadmin.model.backends.mongoengine.view import ModelAdmin


class CustomModelView(ModelAdmin):
    def __init__(self, model, name=None, category=None,
                 endpoint=None, url=None, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

        super(CustomModelView, self).__init__(model, name, category, endpoint,
                                              url)


def setup():
    connect('superadmin_test')
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '1'
    app.config['CSRF_ENABLED'] = False

    admin = Admin(app)

    return app, admin


def test_model():
    app, admin = setup()

    class Person(Document):
        name = StringField()
        age = IntField()

    Person.drop_collection()

    view = CustomModelView(Person)
    admin.add_view(view)

    eq_(view.model, Person)
    eq_(view.name, 'Person')
    eq_(view.endpoint, 'person')

    # Verify form
    with app.test_request_context():
        Form = view.get_form()
        print Form()._fields
        ok_(isinstance(Form()._fields['name'], wtf.TextAreaField))
        ok_(isinstance(Form()._fields['age'], wtf.IntegerField))

    # Make some test clients
    client = app.test_client()

    rv = client.get('/admin/person/')
    eq_(rv.status_code, 200)

    rv = client.get('/admin/person/add/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/person/add/',
                     data=dict(name='name', age='18'))
    eq_(rv.status_code, 302)

    person = Person.objects.first()
    eq_(person.name, 'name')
    eq_(person.age, 18)

    rv = client.get('/admin/person/')
    eq_(rv.status_code, 200)
    ok_(str(person.pk) in rv.data)

    rv = client.get('/admin/person/%s/' % person.pk)
    eq_(rv.status_code, 200)

    rv = client.post('/admin/person/%s/' % person.pk, data=dict(name='changed'))
    eq_(rv.status_code, 302)

    person = Person.objects.first()
    eq_(person.name, 'changed')
    eq_(person.age, 18)

    rv = client.post('/admin/person/%s/delete' % person.pk)
    eq_(rv.status_code, 200)
    eq_(Person.objects.count(), 1)

    rv = client.post('/admin/person/%s/delete' % person.pk, data={'confirm_delete': True})
    eq_(rv.status_code, 302)
    eq_(Person.objects.count(), 0)


def test_list_display():
    app, admin = setup()

    class Person(Document):
        name = StringField()
        age = IntField()

    Person.drop_collection()

    view = CustomModelView(Person, list_display=('name', 'age'))
    admin.add_view(view)

    eq_(len(view.list_display), 2)

    client = app.test_client()

    rv = client.get('/admin/person/')
    ok_('Name' in rv.data)
    ok_('Age' in rv.data)

    rv = client.post('/admin/person/add/',
                     data=dict(name='Steve', age='18'))
    eq_(rv.status_code, 302)

    rv = client.get('/admin/person/')
    ok_('Steve' in rv.data)
    ok_('18' in rv.data)


def test_exclude():
    return
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1, db.session,
                           excluded_list_columns=['test2', 'test4'])
    admin.add_view(view)

    eq_(view._list_columns, [('test1', 'Test1'), ('test3', 'Test3')])

    client = app.test_client()

    rv = client.get('/admin/model1view/')
    ok_('Test1' in rv.data)
    ok_('Test2' not in rv.data)


def test_search_fields():
    return
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1, db.session,
                           searchable_columns=['test1', 'test2'])
    admin.add_view(view)

    eq_(view._search_supported, True)
    eq_(len(view._search_fields), 2)
    ok_(isinstance(view._search_fields[0], db.Column))
    ok_(isinstance(view._search_fields[1], db.Column))
    eq_(view._search_fields[0].name, 'test1')
    eq_(view._search_fields[1].name, 'test2')

    db.session.add(Model1('model1'))
    db.session.add(Model1('model2'))
    db.session.commit()

    client = app.test_client()

    rv = client.get('/admin/model1view/?search=model1')
    ok_('model1' in rv.data)
    ok_('model2' not in rv.data)


def test_url_args():
    return
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1, db.session,
                           page_size=2,
                           searchable_columns=['test1'],
                           column_filters=['test1'])
    admin.add_view(view)

    db.session.add(Model1('data1'))
    db.session.add(Model1('data2'))
    db.session.add(Model1('data3'))
    db.session.add(Model1('data4'))
    db.session.commit()

    client = app.test_client()

    rv = client.get('/admin/model1view/')
    ok_('data1' in rv.data)
    ok_('data3' not in rv.data)

    # page
    rv = client.get('/admin/model1view/?page=1')
    ok_('data1' not in rv.data)
    ok_('data3' in rv.data)

    # sort
    rv = client.get('/admin/model1view/?sort=0&desc=1')
    ok_('data1' not in rv.data)
    ok_('data3' in rv.data)
    ok_('data4' in rv.data)

    # search
    rv = client.get('/admin/model1view/?search=data1')
    ok_('data1' in rv.data)
    ok_('data2' not in rv.data)

    rv = client.get('/admin/model1view/?search=^data1')
    ok_('data2' not in rv.data)

    # like
    rv = client.get('/admin/model1view/?flt0=0&flt0v=data1')
    ok_('data1' in rv.data)

    # not like
    rv = client.get('/admin/model1view/?flt0=1&flt0v=data1')
    ok_('data2' in rv.data)


def test_non_int_pk():
    return
    app, db, admin = setup()

    class Model(db.Model):
        id = db.Column(db.String, primary_key=True)
        test = db.Column(db.String)

    db.create_all()

    view = CustomModelView(Model, db.session, form_columns=['id', 'test'])
    admin.add_view(view)

    client = app.test_client()

    rv = client.get('/admin/modelview/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/modelview/new/',
                     data=dict(id='test1', test='test2'))
    eq_(rv.status_code, 302)

    rv = client.get('/admin/modelview/')
    eq_(rv.status_code, 200)
    ok_('test1' in rv.data)

    rv = client.get('/admin/modelview/edit/?id=test1')
    eq_(rv.status_code, 200)
    ok_('test2' in rv.data)


def test_form():
    # TODO: form_columns
    # TODO: excluded_form_columns
    # TODO: form_args
    pass


def test_field_override():
    return

    app, db, admin = setup()

    class Model(db.Model):
        id = db.Column(db.String, primary_key=True)
        test = db.Column(db.String)

    db.create_all()

    view1 = CustomModelView(Model, db.session, endpoint='view1')
    view2 = CustomModelView(Model, db.session, endpoint='view2', field_overrides=dict(test=wtf.FileField))

    admin.add_view(view1)
    admin.add_view(view2)

    eq_(view1.get_add_form().test.field_class, wtf.TextField)
    eq_(view2.get_add_form().test.field_class, wtf.FileField)


def test_relations():
    # TODO: test relations
    pass

