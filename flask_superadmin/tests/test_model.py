from nose.tools import eq_, ok_

import wtforms

from flask import Flask

from flask_superadmin import Admin
from flask_superadmin.model import base

from flask.ext import wtf


class Model(object):
    def __init__(self, id=None, c1=1, c2=2, c3=3):
        self.id = id
        self.col1 = c1
        self.col2 = c2
        self.col3 = c3

    DoesNotExist = 'dummy'


class Form(wtf.Form):
    col1 = wtforms.TextField()
    col2 = wtforms.TextField()
    col3 = wtforms.TextField()


class MockModelView(base.BaseModelAdmin):

    fields = ('col1', 'col2', 'col3')

    def __init__(self, model, name=None, category=None, endpoint=None,
                 url=None, **kwargs):
        # Allow to set any attributes from parameters
        for k, v in kwargs.items():
            setattr(self, k, v)

        super(MockModelView, self).__init__(model, name, category, endpoint, url)

        self.created_models = []
        self.updated_models = []
        self.deleted_models = []

        self.search_arguments = []

        self.all_models = {1: Model(1),
                           2: Model(2)}
        self.last_id = 3

    # Scaffolding
    def get_pk(self, instance):
        return instance.id

    def get_object(self, pk):
        return self.all_models.get(int(pk))

    def get_objects(self, *pks):
        ret = []
        for pk in pks:
            ret.append(self.all_models.get(int(pk)))
        return ret

    def get_model_form(self):
        def fake_model_form(*args, **kwargs):
            return Form
        return fake_model_form

    def get_converter(self):
        pass

    def scaffold_list_columns(self):
        columns = ['col1', 'col2', 'col3']

        if self.excluded_list_columns:
            return [x for x in columns if x not in self.excluded_list_columns]

        return columns

    def init_search(self):
        return bool(self.searchable_columns)

    def scaffold_sortable_columns(self):
        return ['col1', 'col2', 'col3']

    def scaffold_form(self):
        return Form

    # Data

    def get_list(self, page, sort, sort_desc, search_query):
        self.search_arguments.append((page, sort, sort_desc, search_query))
        return len(self.all_models), iter(self.all_models.values())

    def save_model(self, instance, form, adding=False):
        if adding:
            model = Model(self.last_id)
            self.last_id += 1

            form.populate_obj(model)
            self.created_models.append(model)
            self.all_models[model.id] = model
        else:
            form.populate_obj(instance)
            self.updated_models.append(instance)
        return True

    def update_model(self, form, model):
        return True

    def delete_models(self, *pks):
        for pk in pks:
            self.deleted_models.append(self.all_models.get(int(pk)))
        return True


def setup():
    app = Flask(__name__)
    app.config['WTF_CSRF_ENABLED'] = False
    app.secret_key = '1'
    admin = Admin(app)

    return app, admin


def test_mockview():
    app, admin = setup()

    view = MockModelView(Model)
    admin.add_view(view)

    eq_(view.model, Model)

    eq_(view.name, 'Model')
    eq_(view.url, '/admin/model')
    eq_(view.endpoint, 'model')
    ok_(view.blueprint is not None)

    client = app.test_client()

    # Make model view requests
    rv = client.get('/admin/model/')
    eq_(rv.status_code, 200)

    # Test model creation view
    rv = client.get('/admin/model/add/')
    eq_(rv.status_code, 200)

    rv = client.post('/admin/model/add/',
                     data=dict(col1='test1', col2='test2', col3='test3'))
    eq_(rv.status_code, 302)
    eq_(len(view.created_models), 1)

    model = view.created_models.pop()
    eq_(model.id, 3)
    eq_(model.col1, 'test1')
    eq_(model.col2, 'test2')
    eq_(model.col3, 'test3')

    # Try model edit view
    rv = client.get('/admin/model/3/')
    eq_(rv.status_code, 200)
    ok_('test1' in rv.data)

    rv = client.post('/admin/model/3/',
                     data=dict(col1='test!', col2='test@', col3='test#'))
    eq_(rv.status_code, 302)
    eq_(len(view.updated_models), 1)

    model = view.updated_models.pop()
    eq_(model.col1, 'test!')
    eq_(model.col2, 'test@')
    eq_(model.col3, 'test#')

    rv = client.get('/admin/modelview/4/')
    eq_(rv.status_code, 404)

    # Attempt to delete model
    rv = client.post('/admin/model/3/delete/', data=dict(confirm_delete=True))
    eq_(rv.status_code, 302)
    eq_(rv.headers['location'], 'http://localhost/admin/model/')


def test_permissions():
    app, admin = setup()

    view = MockModelView(Model)
    admin.add_view(view)

    client = app.test_client()

    view.can_create = False
    rv = client.get('/admin/model/add/')
    eq_(rv.status_code, 403)

    view.can_edit = False
    rv = client.get('/admin/model/1/')
    # 200 resp, but readonly fields
    eq_(rv.status_code, 200)
    eq_(rv.data.count('<div class="readonly-value">'), 3)

    view.can_delete = False
    rv = client.post('/admin/model/1/delete/')
    eq_(rv.status_code, 403)


def test_permissions_and_add_delete_buttons():
    app, admin = setup()

    view = MockModelView(Model)
    admin.add_view(view)

    client = app.test_client()

    resp = client.get('/admin/model/')
    eq_(resp.status_code, 200)
    ok_('Add Model' in resp.data)

    view.can_create = False
    resp = client.get('/admin/model/')
    eq_(resp.status_code, 200)
    ok_('Add Model' not in resp.data)

    view.can_edit = False
    view.can_delete = False
    resp = client.get('/admin/model/1/')
    eq_(resp.status_code, 200)
    ok_('Submit' not in resp.data)
    ok_('Save and stay on page' not in resp.data)
    ok_('Delete' not in resp.data)

    view.can_edit = False
    view.can_delete = True
    resp = client.get('/admin/model/1/')
    eq_(resp.status_code, 200)
    ok_('Submit' not in resp.data)
    ok_('Save and stay on page' not in resp.data)
    ok_('Delete' in resp.data)

    view.can_edit = True
    view.can_delete = False
    resp = client.get('/admin/model/1/')
    eq_(resp.status_code, 200)
    ok_('Submit' in resp.data)
    ok_('Save and stay on page' in resp.data)
    ok_('Delete' not in resp.data)


def test_templates():
    app, admin = setup()

    view = MockModelView(Model)
    admin.add_view(view)

    client = app.test_client()

    view.list_template = 'mock.html'
    view.add_template = 'mock.html'
    view.edit_template = 'mock.html'

    rv = client.get('/admin/model/')
    eq_(rv.data, 'Success!')

    rv = client.get('/admin/model/add/')
    eq_(rv.data, 'Success!')

    rv = client.get('/admin/model/1/')
    eq_(rv.data, 'Success!')


def test_list_display_header():
    app, admin = setup()

    view = MockModelView(Model, list_display=['test_header'])
    admin.add_view(view)

    eq_(len(view.list_display), 1)

    client = app.test_client()

    rv = client.get('/admin/model/')
    ok_('Test Header' in rv.data)


def test_search_fields():
    app, admin = setup()

    view = MockModelView(Model, search_fields=['col1', 'col2'])
    admin.add_view(view)

    eq_(view.search_fields, ['col1', 'col2'])

    client = app.test_client()

    rv = client.get('/admin/model/')
    ok_('<div class="search">' in rv.data)

