from nose.tools import ok_, eq_, raises

from flask import Flask
from flask_superadmin import base


class MockView(base.BaseView):
    # Various properties
    allow_call = True
    allow_access = True

    @base.expose('/')
    def index(self):
        return 'Success!'

    @base.expose('/test/')
    def test(self):
        return self.render('mock.html')

    def _handle_view(self, name, **kwargs):
        if self.allow_call:
            return super(MockView, self)._handle_view(name, **kwargs)
        else:
            return 'Failure!'

    def is_accessible(self):
        if self.allow_access:
            return super(MockView, self).is_accessible()
        else:
            return False


def test_baseview_defaults():
    view = MockView()
    eq_(view.name, None)
    eq_(view.category, None)
    eq_(view.endpoint, None)
    eq_(view.url, None)
    eq_(view.static_folder, None)
    eq_(view.admin, None)
    eq_(view.blueprint, None)


def test_base_defaults():
    admin = base.Admin()
    eq_(admin.name, 'Admin')
    eq_(admin.url, '/admin')
    eq_(admin.app, None)
    ok_(admin.index_view is not None)

    # Check if default view was added
    eq_(len(admin._views), 1)
    eq_(admin._views[0], admin.index_view)


def test_base_registration():
    app = Flask(__name__)
    admin = base.Admin(app)

    eq_(admin.app, app)
    ok_(admin.index_view.blueprint is not None)


def test_admin_customizations():
    app = Flask(__name__)
    admin = base.Admin(app, name='Test', url='/foobar')
    eq_(admin.name, 'Test')
    eq_(admin.url, '/foobar')

    client = app.test_client()
    rv = client.get('/foobar/')
    eq_(rv.status_code, 200)


def test_baseview_registration():
    admin = base.Admin()

    view = MockView()
    bp = view.create_blueprint(admin)

    # Base properties
    eq_(view.admin, admin)
    ok_(view.blueprint is not None)

    # Calculated properties
    eq_(view.endpoint, 'mockview')
    eq_(view.url, '/admin/mockview')
    eq_(view.name, 'Mock View')

    # Verify generated blueprint properties
    eq_(bp.name, view.endpoint)
    eq_(bp.url_prefix, view.url)
    eq_(bp.template_folder, 'templates')
    eq_(bp.static_folder, view.static_folder)

    # Verify customizations
    view = MockView(name='Test', endpoint='foobar')
    view.create_blueprint(base.Admin())

    eq_(view.name, 'Test')
    eq_(view.endpoint, 'foobar')
    eq_(view.url, '/admin/foobar')

    view = MockView(url='test')
    view.create_blueprint(base.Admin())
    eq_(view.url, '/admin/test')

    view = MockView(url='/test/test')
    view.create_blueprint(base.Admin())
    eq_(view.url, '/test/test')


def test_baseview_urls():
    app = Flask(__name__)
    admin = base.Admin(app)

    view = MockView()
    admin.add_view(view)

    eq_(len(view._urls), 2)


@raises(Exception)
def test_no_default():
    app = Flask(__name__)
    admin = base.Admin(app)
    admin.add_view(base.BaseView())


def test_call():
    app = Flask(__name__)
    admin = base.Admin(app)
    view = MockView()
    admin.add_view(view)
    client = app.test_client()

    rv = client.get('/admin/')
    eq_(rv.status_code, 200)

    rv = client.get('/admin/mockview/')
    eq_(rv.data, 'Success!')

    rv = client.get('/admin/mockview/test/')
    eq_(rv.data, 'Success!')

    # Check authentication failure
    view.allow_call = False
    rv = client.get('/admin/mockview/')
    eq_(rv.data, 'Failure!')


def test_permissions():
    app = Flask(__name__)
    admin = base.Admin(app)
    view = MockView()
    admin.add_view(view)
    client = app.test_client()

    view.allow_access = False

    rv = client.get('/admin/mockview/')
    eq_(rv.status_code, 403)


def test_submenu():
    app = Flask(__name__)
    admin = base.Admin(app)
    admin.add_view(MockView(name='Test 1', category='Test', endpoint='test1'))

    # Second view is not normally accessible
    view = MockView(name='Test 2', category='Test', endpoint='test2')
    view.allow_access = False
    admin.add_view(view)

    ok_('Test' in admin._menu_categories)
    eq_(len(admin._menu), 2)
    eq_(admin._menu[1].name, 'Test')
    eq_(len(admin._menu[1]._children), 2)

    # Categories don't have URLs and they're not accessible
    eq_(admin._menu[1].get_url(), None)
    eq_(admin._menu[1].is_accessible(), False)

    eq_(len(admin._menu[1].get_children()), 1)


def test_delayed_init():
    app = Flask(__name__)
    admin = base.Admin()
    admin.add_view(MockView())
    admin.init_app(app)

    client = app.test_client()

    rv = client.get('/admin/mockview/')
    eq_(rv.data, 'Success!')


@raises(Exception)
def test_double_init():
    app = Flask(__name__)
    admin = base.Admin(app)
    admin.init_app(app)

