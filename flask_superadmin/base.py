import re

from functools import wraps

from flask import Blueprint, render_template, url_for, abort

from flask_superadmin import babel


def expose(url='/', methods=('GET',)):
    """
        Use this decorator to expose views in your view classes.

        `url`
            Relative URL for the view
        `methods`
            Allowed HTTP methods. By default only GET is allowed.
    """
    def wrap(f):
        if not hasattr(f, '_urls'):
            f._urls = []
        f._urls.append((url, methods))
        return f

    return wrap


# Base views
def _wrap_view(f):
    @wraps(f)
    def inner(self, *args, **kwargs):
        h = self._handle_view(f.__name__, *args, **kwargs)

        if h is not None:
            return h

        return f(self, *args, **kwargs)

    return inner


class AdminViewMeta(type):
    """
        View metaclass.

        Does some precalculations (like getting list of view methods from the class) to avoid
        calculating them for each view class instance.
    """
    def __init__(cls, classname, bases, fields):
        type.__init__(cls, classname, bases, fields)

        # Gather exposed views
        cls._urls = []
        cls._default_view = None

        for p in dir(cls):
            attr = getattr(cls, p)

            if hasattr(attr, '_urls'):
                # Collect methods
                for url, methods in attr._urls:
                    cls._urls.append((url, p, methods))

                    if url == '/':
                        cls._default_view = p

                # Wrap views
                setattr(cls, p, _wrap_view(attr))


class BaseView(object, metaclass=AdminViewMeta):
    """
        Base administrative view.

        Derive from this class to implement your administrative interface piece. For example::

            class MyView(BaseView):
                @expose('/')
                def index(self):
                    return 'Hello World!'
    """

    def __init__(self, name=None, category=None, endpoint=None, url=None, static_folder=None):
        """
            Constructor.

            `name`
                Name of this view. If not provided, will be defaulted to the class name.
            `category`
                View category. If not provided, will be shown as a top-level menu item. Otherwise, will
                be in a submenu.
            `endpoint`
                Base endpoint name for the view. For example, if there's view method called "index" and
                endpoint was set to "myadmin", you can use `url_for('myadmin.index')` to get URL to the
                view method. By default, equals to the class name in lower case.
            `url`
                Base URL. If provided, affects how URLs are generated. For example, if url parameter
                equals to "test", resulting URL will look like "/admin/test/". If not provided, will
                use endpoint as a base url. However, if URL starts with '/', absolute path is assumed
                and '/admin/' prefix won't be applied.
        """
        self.name = name
        self.category = category
        self.endpoint = endpoint
        self.url = url
        self.static_folder = static_folder

        # Initialized from create_blueprint
        self.admin = None
        self.blueprint = None

        # Default view
        if self._default_view is None:
            raise Exception('Attempted to instantiate admin view %s without default view' % self.__class__.__name__)

    def create_blueprint(self, admin):
        """ Create Flask blueprint. """

        # Store admin instance
        self.admin = admin

        # If endpoint name is not provided, get it from the class name
        if self.endpoint is None:
            self.endpoint = self.__class__.__name__.lower()

        # If url is not provided, generate it from endpoint name
        if self.url is None:
            self.url = '%s/%s' % (self.admin.url, self.endpoint)
        else:
            if not self.url.startswith('/'):
                self.url = '%s/%s' % (self.admin.url, self.url)

        # If name is not povided, use capitalized endpoint name
        if self.name is None:
            self.name = self._prettify_name(self.__class__.__name__)

        # Create blueprint and register rules
        self.blueprint = Blueprint(self.endpoint, __name__,
                                   url_prefix=self.url,
                                   template_folder='templates',
                                   static_folder=self.static_folder)

        for url, name, methods in self._urls:
            self.blueprint.add_url_rule(url,
                                        name,
                                        getattr(self, name),
                                        methods=methods)

        return self.blueprint

    def render(self, template, **kwargs):
        """
            Render template

            `template`
                Template path to render
            `kwargs`
                Template arguments
        """
        # Store self as admin_view
        kwargs['admin_view'] = self

        # Provide i18n support even if flask-babel is not installed
        # or enabled.
        kwargs['_gettext'] = babel.gettext
        kwargs['_ngettext'] = babel.ngettext

        return render_template(template, **kwargs)

    def _prettify_name(self, name):
        """
            Prettify class name by splitting name by capital characters. So, 'MySuperClass' will look like 'My Super Class'

            `name`
                String to prettify
        """
        return re.sub(r'(?<=.)([A-Z])', r' \1', name)

    def is_accessible(self):
        """
            Override this method to add permission checks.

            Flask-SuperAdmin does not make any assumptions about authentication system used in your application, so it is
            up for you to implement it.

            By default, it will allow access for the everyone.
        """
        return True

    def _handle_view(self, name, *args, **kwargs):
        if not self.is_accessible():
            return abort(403)


class AdminIndexView(BaseView):
    """
        Default administrative interface index page when visiting the ``/admin/`` URL.

        It can be overridden by passing your own view class to the ``Admin`` constructor::

            class MyHomeView(AdminIndexView):
                @expose('/')
                def index(self):
                    return render_template('adminhome.html')

            admin = Admin(index_view=MyHomeView)

        Default values for the index page are following:

        * If name is not provided, 'Home' will be used.
        * If endpoint is not provided, will use ``admin``
        * Default URL route is ``/admin``.
        * Automatically associates with static folder.
    """
    def __init__(self, name=None, category=None, endpoint=None, url=None):
        super(AdminIndexView, self).__init__(name or babel.lazy_gettext('Home'),
                                             category,
                                             endpoint or 'admin',
                                             url or '/admin',
                                             'static')

    @expose('/')
    def index(self):
        return self.render('admin/index.html')


class MenuItem(object):
    """ Simple menu tree hierarchy. """

    def __init__(self, name, view=None):
        self.name = name
        self._view = view
        self._children = []
        self._children_urls = set()
        self._cached_url = None

        self.url = None
        if view is not None:
            self.url = view.url

    def add_child(self, view):
        self._children.append(view)
        self._children_urls.add(view.url)

    def get_url(self):
        if self._view is None:
            return None

        if self._cached_url:
            return self._cached_url

        self._cached_url = url_for('%s.%s' % (self._view.endpoint, self._view._default_view))
        return self._cached_url

    def is_active(self, view):
        if view == self._view:
            return True

        return view.url in self._children_urls

    def is_accessible(self):
        if self._view is None:
            return False

        return self._view.is_accessible()

    def is_category(self):
        return self._view is None

    def get_children(self):
        return [c for c in self._children if c.is_accessible()]


class Admin(object):
    """ Collection of the views. Also manages menu structure. """
    app = None

    def __init__(self, app=None, name=None, url=None, index_view=None,
                 translations_path=None):
        """
            Constructor.

            `app`
                Flask application object
            `name`
                Application name. Will be displayed in main menu and as a page title. If not provided, defaulted to "Admin"
            `index_view`
                Home page view to use. If not provided, will use `AdminIndexView`.
            `translations_path`
                Location of the translation message catalogs. By default will use translations
                shipped with the Flask-SuperAdmin.
        """
        self.translations_path = translations_path

        self._views = []
        self._menu = []
        self._menu_categories = dict()
        self._models = []
        self._model_backends = list()

        try:
            from flask_superadmin.model.backends import mongoengine
            self.add_model_backend(mongoengine.ModelAdmin)
        except:
            pass

        try:
            from flask_superadmin.model.backends import sqlalchemy
            self.add_model_backend(sqlalchemy.ModelAdmin)
        except:
            pass

        try:
            from flask_superadmin.model.backends import django
            self.add_model_backend(django.ModelAdmin)
        except:
            pass

        if name is None:
            name = 'Admin'
        self.name = name

        if url is None:
            url = '/admin'
        self.url = url

        # Localizations
        self.locale_selector_func = None

        # Add predefined index view
        self.index_view = index_view or AdminIndexView(url=self.url)
        self.add_view(self.index_view)

        if app is not None:
            self.init_app(app)

    def model_backend(self, model):
        for backend in self._model_backends:
            if backend.model_detect(model):
                return backend
        raise Exception('There is no backend for this model')

    def add_model_backend(self, backend):
        self._model_backends.append(backend)

    def register(self, model, admin_class=None, *args, **kwargs):
        """
            Register model to the collection.

            `model`
                Model to add.
            `admin_class`
                ModelAdmin class corresponding to model.
        """
        from flask_superadmin.model import ModelAdmin

        admin_class = admin_class or ModelAdmin

        backend = self.model_backend(model)
        new_class = type(admin_class.__name__, (admin_class, backend), {})
        model_view = new_class(model, *args, **kwargs)

        self._models.append((model, model_view))
        self.add_view(model_view)

    def add_view(self, view):
        """
            Add view to the collection.

            `view`
                View to add.
        """
        # Add to views
        self._views.append(view)

        # If app was provided in constructor, register view with Flask app
        if self.app is not None:
            self.app.register_blueprint(view.create_blueprint(self))
            self._add_view_to_menu(view)

    def locale_selector(self, f):
        """
            Installs locale selector for current ``Admin`` instance.

            Example::

                def admin_locale_selector():
                    return request.args.get('lang', 'en')

                admin = Admin(app)
                admin.locale_selector(admin_locale_selector)

            It is also possible to use the ``@admin`` decorator::

                admin = Admin(app)

                @admin.locale_selector
                def admin_locale_selector():
                    return request.args.get('lang', 'en')

            Or by subclassing the ``Admin``::

                class MyAdmin(Admin):
                    def locale_selector(self):
                        return request.args.get('lang', 'en')
        """
        if self.locale_selector_func is not None:
            raise Exception('Can not add locale_selector second time.')

        self.locale_selector_func = f

    def _add_view_to_menu(self, view):
        """
            Add view to the menu tree

            `view`
                View to add
        """
        if view.category:
            category = self._menu_categories.get(view.category)

            if category is None:
                category = MenuItem(view.category)
                self._menu_categories[view.category] = category
                self._menu.append(category)

            category.add_child(MenuItem(view.name, view))
        else:
            self._menu.append(MenuItem(view.name, view))

    def init_app(self, app):
        """
            Register all views with Flask application.

            `app`
                Flask application instance
        """
        self.app = app

        app.extensions = getattr(app, 'extensions', {})
        app.extensions['admin'] = self

        for view in self._views:
            app.register_blueprint(view.create_blueprint(self))
            self._add_view_to_menu(view)

    def menu(self):
        """ Return menu hierarchy. """
        return self._menu
