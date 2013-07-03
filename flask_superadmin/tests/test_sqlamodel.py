from nose.tools import eq_, ok_, raises

from flask import Flask

from flask.ext import wtf

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import InvalidRequestError
from flask_superadmin import Admin
from flask_superadmin.model.backends.sqlalchemy.view import ModelAdmin


class CustomModelView(ModelAdmin):
    def __init__(self, model, session, name=None, category=None,
                 endpoint=None, url=None, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

        super(CustomModelView, self).__init__(model, session, name, category,
                                              endpoint, url)


def create_models(db):
    class Model1(db.Model):
        def __init__(self, test1=None, test2=None, test3=None, test4=None):
            self.test1 = test1
            self.test2 = test2
            self.test3 = test3
            self.test4 = test4

        id = db.Column(db.Integer, primary_key=True)
        test1 = db.Column(db.String(20))
        test2 = db.Column(db.Unicode(20))
        test3 = db.Column(db.Text)
        test4 = db.Column(db.UnicodeText)

    class Model2(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        int_field = db.Column(db.Integer)
        bool_field = db.Column(db.Boolean)

    db.create_all()

    return Model1, Model2


def setup():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '1'
    app.config['CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'

    db = SQLAlchemy(app)
    admin = Admin(app)

    return app, db, admin


def test_model():
    app, db, admin = setup()
    Model1, Model2 = create_models(db)
    db.create_all()

    view = CustomModelView(Model1, db.session)
    admin.add_view(view)

    eq_(view.model, Model1)
    eq_(view.name, 'Model1')
    eq_(view.endpoint, 'model1')

    eq_(view._primary_key, 'id')

    # Verify form
    eq_(view.get_form()._fields['test_1'], wtf.TextField)
    eq_(view.get_form()._fields['test_2'], wtf.TextField)
    eq_(view.get_form()._fields['test_3'], wtf.TextAreaField)
    eq_(view.get_form()._fields['test_4'], wtf.TextAreaField)

    # Make some test clients
    client = app.test_client()

    rv = client.get('/admin/model1/')
    eq_(rv.status_code, 200)

    rv = client.get('/admin/model1/add/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/model1/add/',
                     data=dict(test1='test1large', test2='test2'))
    eq_(rv.status_code, 302)

    model = db.session.query(Model1).first()
    eq_(model.test1, 'test1large')
    eq_(model.test2, 'test2')
    eq_(model.test3, '')
    eq_(model.test4, '')

    rv = client.get('/admin/model1/')
    eq_(rv.status_code, 200)
    ok_('test1large' in rv.data)

    rv = client.get('/admin/model1/edit/%s/' % model.id)
    eq_(rv.status_code, 200)

    rv = client.post(url, data=dict(test1='test1small', test2='test2large'))
    eq_(rv.status_code, 302)

    model = db.session.query(Model1).first()
    eq_(model.test1, 'test1small')
    eq_(model.test2, 'test2large')
    eq_(model.test3, '')
    eq_(model.test4, '')

    rv = client.post('/admin/model1/%s/delete/' % model.id)
    eq_(rv.status_code, 302)
    eq_(db.session.query(Model1).count(), 0)


@raises(InvalidRequestError)
def test_no_pk():
    app, db, admin = setup()

    class Model(db.Model):
        test = db.Column(db.Integer)

    view = CustomModelView(Model, db.session)
    admin.add_view(view)


def test_list_display():
    return
    app, db, admin = setup()

    Model1, Model2 = create_models(db)

    view = CustomModelView(Model1, db.session,
                           list_columns=['test1', 'test3'],
                           rename_columns=dict(test1='Column1'))
    admin.add_view(view)

    eq_(len(view._list_columns), 2)
    eq_(view._list_columns, [('test1', 'Column1'), ('test3', 'Test3')])

    client = app.test_client()

    rv = client.get('/admin/model1view/')
    ok_('Column1' in rv.data)
    ok_('Test2' not in rv.data)


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

