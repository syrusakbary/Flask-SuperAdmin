from flask import request, url_for, redirect, flash, abort

from flask_superadmin.babel import gettext

from flask_superadmin.base import BaseView, expose
from flask_superadmin.tools import rec_getattr
from flask_superadmin.model import filters

# from flask_superadmin.form import format_form

from flask_superadmin.form import ChosenSelectWidget, DatePickerWidget, DateTimePickerWidget

from wtforms import fields,widgets

class AdminModelConverter(object):
    def convert(self,*args,**kwargs):
        field = super(AdminModelConverter,self).convert(*args,**kwargs)
        if field:
            widget = field.kwargs.get('widget',field.field_class.widget)
            print field, widget
            if isinstance(widget,widgets.Select):
                field.kwargs['widget'] = ChosenSelectWidget(multiple=widget.multiple)
            elif issubclass(field.field_class, fields.DateTimeField):
                field.kwargs['widget'] = DateTimePickerWidget()
            elif issubclass(field.field_class, fields.DateField):
                field.kwargs['widget'] = DatePickerWidget()
        return field

def prettify(str):
    return str.replace('_', ' ').title()

class BaseModelAdmin(BaseView):
    """
    BaseModelView provides create/edit/delete functionality for a peewee Model.
    """
    # columns to display in the list index - can be field names or callables on
    # a model instance, though in the latter case they will not be sortable
    list_per_page = 20
    list_display = tuple()

    # form parameters, lists of fields
    exclude = None
    only = None
    fields = None

    form = None

    can_edit = True
    can_create = True
    can_delete = True

    list_template = 'admin/model/list.html'
    edit_template = 'admin/model/edit.html'
    add_template = 'admin/model/add.html'
    delete_template = 'admin/model/delete.html'

    search_fields = None
    actions = None

    field_args = None

    @staticmethod
    def model_detect(model):
        return False

    def __init__(self, model=None, name=None, category=None, endpoint=None, url=None):
        if name is None:
            name = '%s' % prettify(model.__name__)

        if endpoint is None:
            endpoint = ('%s' % model.__name__).lower()

        super(BaseModelAdmin, self).__init__(name, category, endpoint, url)

        if model: self.model = model

    def get_display_name(self):
        return self.model.__name__

    def allow_pk(self):
        return not self.model._meta.auto_increment

    def get_form(self, adding=False):
        allow_pk = adding and self.allow_pk()
        return model_form(self.model, only=self.fields, exclude=self.exclude, converter=CustomModelConverter(self))

    def get_add_form(self):
        return self.get_form(adding=True)

    def get_edit_form(self):
        return self.get_form()

    def get_objects(self,*pks):
        raise NotImplemented()

    def get_object(self,pk):
        raise NotImplemented()

    def get_pk (self,instance):
        return

    def save_model(self, instance, form, adding=False):
        raise NotImplemented()

    def delete_models(self, *pks):
        raise NotImplemented()

    def is_sortable(self, column):
        return False

    def field_name(self, field):
        return prettify(field)

    def get_list(sel):
        raise NotImplemented()

    def get_url_name(self,name):
        URLS = {
            'index':'.list',
            'add':'.add',
            'delete':'.delete',
            'edit':'.edit'
        }
        return URLS[name]

    def dispatch_save_redirect(self, instance):
        return_url = request.args.get('next',None) or self.get_url_name('index')
        if 'save' in request.form:
            return redirect(url_for(self.get_url_name('index')))
        elif 'save_add' in request.form:
            return redirect(url_for(self.get_url_name('add')))
        else:
            return redirect(
                url_for(self.get_url_name('edit'), pk=self.get_pk(instance))
            )

    @expose('/add/', methods=('GET', 'POST'))
    def add(self):
        Form = self.get_add_form()
        if request.method == 'POST':
            form = Form(request.form)
            if form.validate():
                try:
                    instance = self.save_model(self.model(), form, True)
                    flash(gettext('New %(model)s saved successfully', model= self.get_display_name()), 'success')
                    return self.dispatch_save_redirect(instance)
                except Exception, ex:
                    self.session.rollback()
                    flash(gettext('Failed to add model. %(error)s', error=str(ex)), 'error')
        else:
            form = Form(obj=self.model())

        return self.render(self.add_template, model=self.model, form=form)

    @property
    def page (self):
        return request.args.get('page', 0, type=int)

    @property
    def sort (self):
        return request.args.get('sort', None, type=int), request.args.get('desc', None, type=bool)

    @property
    def search (self):
        return request.args.get('search', None)

    @expose('/', methods=('GET','POST',))
    def list(self):
        """
            List view
        """
        # Grab parameters from URL
        if request.method == 'POST':
            id_list = request.form.getlist('_selected_action')
            if id_list and (request.form.get('action-delete') or request.form.get('action',None)=='delete'):
                return self.delete(*id_list)
        count, data = self.get_list()
        return self.render(self.list_template, data=data, count=count, modeladmin=self)

    @expose('/<pk>/', methods=('GET', 'POST'))
    def edit(self,pk):
        try:
            instance = self.get_object(pk)
        except self.DoesNotExist:
            abort(404)

        Form = self.get_edit_form()

        if request.method == 'POST':
            form = Form(request.form, obj=instance)
            if form.validate():
                try:
                    self.save_model(instance, form, False)
                    flash('Changes to %s saved successfully' % self.get_display_name(), 'success')
                    return self.dispatch_save_redirect(instance)
                except Exception, ex:
                    flash(gettext('Failed to edit model. %(error)s', error=str(ex)), 'error')
        else:
            form = Form(obj=instance)

        return self.render(self.edit_template, model=self.model, form=form, pk=self.get_pk(instance))


    @expose('/<pk>/delete', methods=('GET', 'POST'))
    def delete(self,pk=None,*pks):
        if pk: pks += pk,
            # collected = {}
            # if self.delete_collect_objects:
            #     for obj in query:
            #         collected[obj.get_pk()] = self.collect_objects(obj)

        if request.method == 'POST' and 'confirm_delete' in request.form:
            count = len(pks)
            self.delete_models(*pks)

            flash('Successfully deleted %s %ss' % (count, self.get_display_name()), 'success')
            return redirect(url_for(self.get_url_name('index')))
        else:
            instances = self.get_objects(*pks)

        return self.render(self.delete_template,
            instances=instances
            # query=query,
            # collected=collected,
        )

class ModelAdmin(object):
    def __new__ (cls, admin, model,*args,**kwargs):
        backend_model_class = admin.model_backend(model)
        d = dict(cls.__dict__)
        if cls != ModelAdmin:
            bases = tuple(map(lambda x: x if x != ModelAdmin else backend_model_class,cls.__bases__))
            new_class = type(cls.__name__, bases, d)
            # print d,bases
        else: new_class = backend_model_class
        # print new_class,new_class.__class__,backend_model_class
        return new_class(model,*args,**kwargs)
